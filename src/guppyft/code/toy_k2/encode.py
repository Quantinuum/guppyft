"""Builder and encoding implementation for the ToyK2 architecture."""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Self, no_type_check, overload

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder, EmulatorInstance
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.builtins import array, comptime, exit, owned
from guppylang.std.collections import Stack, empty_stack
from guppylang.std.option import Option, nothing, some
from hugr.ext import ExtensionRegistry
from hugr.package import Package
from hugr.std import _std_extensions

from guppyft.code.toy_k2 import primitives as k2_primitives
from guppyft.encode import (
    EncoderParams,
    EncodeSpec,
    ImplementOps,
    ImplementOpsSpec,
    OpReplacements,
    ReplacementCompiler,
    TyReplacements,
    encode,
)
from guppyft.extensions import std_ops, std_types, toy_k2_ops, toy_k2_types
from guppyft.globals import map_global, with_global
from guppyft.std import LogicalBlock

N = guppy.nat_var("N")


@dataclass(frozen=True, kw_only=True)
class ToyK2EncoderParams(EncoderParams):
    """Parameters for a ToyK2 encoding.

    Attributes:
        n_blocks: Number of logical blocks available to the encoding.
    """

    n_blocks: int

    def encoding(self) -> str:
        """Return the identifier for the ToyK2 encoding."""
        return "toy_k2"

    def params(self) -> Mapping[str, Any]:
        """Return the ToyK2-specific encoding parameters."""
        return {"n_blocks": self.n_blocks}


@dataclass
class QEDPolicy:
    """Policy to determine when QED cycles are injected.

    Each logical block accumulates a cost based on `costs`. Once a
    block's accumulated cost reaches `threshold` a QED cycle
    is performed on that block and its counter is reset.

    Attributes:
        threshold: Threshold at which a QED cycle is triggered.
        costs: See `OperationCosts`.
    """

    class OperationCosts:
        """Configuration for operation costs. Used e.g. for applying QED cycles."""

        prep_zero_ft: float = 0.0
        prep_y_states_non_ft: float = 0.0
        prep_t_states_non_ft: float = 0.0
        x: float = 0.0
        z: float = 0.0
        h_all: float = 0.0
        cx_intra: float = 0.0
        cx_transversal: float = 0.0
        swap_intra: float = 0.0
        measure_z_all: float = 0.0
        measure_z: float = 0.0

        def __setattr__(self, key: str, value: Any) -> None:
            """Set a non-negative cost for a known logical operation."""
            if not hasattr(self, key):
                raise KeyError(f"Unknown cost key: {key}")
            if value < 0:
                raise ValueError(f"Op cost cannot be negative: received {value}")
            super().__setattr__(key, value)

    threshold: int = 1
    costs: OperationCosts = field(default_factory=OperationCosts)


@dataclass(frozen=True)
class ToyK2Instance:
    """A ToyK2 architecture instance built by `ToyK2Builder.build`."""

    _spec: EncodeSpec

    @overload
    def encode(self, pkg: Package, *, as_bytes: Literal[False] = False) -> Package: ...
    @overload
    def encode(self, pkg: Package, *, as_bytes: Literal[True]) -> bytes: ...
    def encode(self, pkg: Package, *, as_bytes: bool = False) -> Package | bytes:
        """Encode a computational package with the ToyK2 instance."""
        self.check_may_encode(pkg)
        pkg_bytes: Package | bytes = encode(pkg, self._spec, as_bytes=as_bytes)  # type: ignore[call-overload]
        return pkg_bytes

    @overload
    def implement_ops(
        self, pkg: Package, *, as_bytes: Literal[False] = False
    ) -> Package: ...
    @overload
    def implement_ops(self, pkg: Package, *, as_bytes: Literal[True]) -> bytes: ...
    def implement_ops(self, pkg: Package, *, as_bytes: bool = False) -> Package | bytes:
        """Implement logical ops in `pkg` using this instance's op implementations."""
        assert self._spec.implement_ops is not None
        pkg_bytes: Package | bytes = self._spec.implement_ops(pkg, as_bytes=as_bytes)  # type: ignore[call-overload]
        return pkg_bytes

    def check_may_encode(self, hugr: Package) -> None:
        """Check whether any issues can be detected that would arise when trying to
        encode the given package, e.g. the package containing unsupported gates.

        Note that this function returning without error is not a guarantee that a
        subsequent call to `encode` will succeed."""
        assert self._spec.compile is not None
        if (error := self._spec.compile.check_may_compile(hugr)) is not None:
            raise error

    def emulator(
        self,
        pkg: Package,
        n_qubits: int,
        builder: EmulatorBuilder | None = None,
    ) -> EmulatorInstance:
        """Encode a hugr Package and build an emulator for it.

        Args:
            pkg: The computational hugr package.
            n_qubits: Number of physical qubits available to the emulator.
            builder: Optional `EmulatorBuilder` to use; defaults to a new one.
        """
        encoded_pkg = self.encode(pkg, as_bytes=True)
        if builder is None:
            builder = EmulatorBuilder()
        return builder.build(encoded_pkg, n_qubits)


@dataclass(frozen=True, kw_only=True)
class ToyK2Builder:
    """ToyK2 architecture builder class for creating `ToyK2Instance` objects."""

    _qed_policy: QEDPolicy = field(default_factory=QEDPolicy)

    @classmethod
    def from_params(cls, params: ToyK2EncoderParams) -> ToyK2Instance:
        """Build a ToyK2 instance from encoding parameters."""
        return cls().build(params.n_blocks)

    def _gen_implement_spec(self, n_blocks: int) -> ImplementOpsSpec:
        """Generate the `ImplementOpsSpec` providing ToyK2 implementations of
        logical ops for a program using `n_blocks` logical blocks."""
        qed_policy = self._qed_policy

        @guppy.struct
        class RuntimeBlock:
            """Represents a logical block at runtime for the ToyK2 architecture.

            Attributes:
                logical_block: The logical block contained in this runtime block.
                borrowed_addr: Indicates which addresses have been borrowed.
                qed_counter: The QED counter associated with this runtime block.
            """

            logical_block: LogicalBlock[4]  # type: ignore[valid-type, type-arg]
            borrowed_addr: array[bool, 2]  # type: ignore[valid-type]
            qed_counter: float

            @guppy
            @no_type_check
            def borrow_addr(self, qb_id: int) -> None:
                """Mark the address as borrowed."""
                if self.borrowed_addr[qb_id]:
                    exit("borrow_addr: Address is already borrowed")
                self.borrowed_addr[qb_id] = True

            @guppy
            @no_type_check
            def restore_addr(self, qb_id: int) -> None:
                """Restore the borrowed address."""
                if not self.borrowed_addr[qb_id]:
                    exit("restore_addr: Cannot restore non-borrowed address")
                self.borrowed_addr[qb_id] = False

            @guppy
            @no_type_check
            def is_borrowed(self) -> bool:
                """Check if any address in the block is borrowed."""
                return self.borrowed_addr[0] or self.borrowed_addr[1]

            @guppy
            @no_type_check
            def discard(self) -> None:
                """Discard the runtime block, releasing any resources."""
                self.logical_block.discard()

        @guppy.struct
        class STATE:
            """Tracks the global context for the ToyK2 architecture at runtime.

            Attributes:
                blocks: Stores the runtime blocks.
                unalloc_blks: Stack of block that have not yet been allocated.
                avail_dyn_addrs: Stack of available addresses on existing dynamic
                    blocks.
            """

            blocks: array[Option[RuntimeBlock], comptime(n_blocks)]  # type: ignore[valid-type]
            unalloc_blks: Stack[int, comptime(n_blocks)]  # type: ignore[valid-type]
            avail_dyn_addrs: Stack[tuple[int, int], comptime(n_blocks)]  # type: ignore[valid-type]

            @guppy
            @no_type_check
            def take_block(self, blk_id: int) -> RuntimeBlock:
                return self.blocks[blk_id].take().unwrap()

            @guppy
            @no_type_check
            def put_block(self, blk_id: int, blk: RuntimeBlock @ owned) -> None:
                self.blocks[blk_id].swap(some(blk)).unwrap_nothing()

            @guppy
            @no_type_check
            def release_block(self, blk_id: int) -> LogicalBlock[4]:
                """Consumes the RuntimeBlock and returns its logical block."""
                runtime_block = self.take_block(blk_id)
                self.unalloc_blks.push(blk_id)
                return runtime_block.logical_block

            @guppy
            @no_type_check
            def allocate_block(self, logical_block: LogicalBlock[4] @ owned) -> int:
                """Reserve a new RuntimeBlock containing the given LogicalBlock."""
                if len(self.unalloc_blks) == 0:
                    exit("allocate_blk_id: No more logical blocks to allocate")
                blk_id = self.unalloc_blks.pop()

                runtime_block = RuntimeBlock(logical_block, array(False, False), 0.0)
                self.put_block(blk_id, runtime_block)

                return blk_id

            @guppy
            @no_type_check
            def release_dyn_addr(self, addr: tuple[int, int]) -> None:
                """Restore the dynamic logical qubit back to its block and
                free the block if it is fully restored."""
                blk_id, qb_id = addr
                # Restore the block's address
                self.blocks[blk_id].restore_addr(qb_id)
                # Check if the block is fully restored
                if not self.blocks[blk_id].is_borrowed():
                    # Release the runtime block
                    logical_block = self.release_block(blk_id)
                    # Free the logical block
                    logical_block.discard()
                    # Remove the remaining addresses of this block from the stack
                    # NOTE: Ideally, `avail_dyn_addrs` would be a data
                    # structure with fast deletion (e.g. a set).
                    # Generally, this stack will be small, though, so it
                    # shouldn't be a performance bottleneck.
                    aux_stack: Stack[int, comptime(n_blocks)] = empty_stack()
                    for _ in range(len(self.avail_dyn_addrs)):
                        addr = self.avail_dyn_addrs.pop()
                        if addr[0] != blk_id:
                            aux_stack.push(addr)
                    for addr in aux_stack:
                        self.avail_dyn_addrs.push(addr)

            @guppy
            @no_type_check
            def allocate_dyn_addr(self: "STATE") -> tuple[int, int]:
                """Find or create a dynamic block and return an address from
                it to be used as a dynamic logical qubit."""
                if len(self.avail_dyn_addrs) > 0:
                    blk_id, qb_id = self.avail_dyn_addrs.pop()
                else:
                    # Otherwise, prepare a new block
                    logical_block = k2_primitives.prep_zero_ft()
                    blk_id = self.allocate_block(logical_block)
                    # The first address will be returned
                    qb_id = 0
                    # And the other address is added to the stack
                    self.avail_dyn_addrs.push((blk_id, 1))

                # Borrow the selected address from the dynamic block
                self.blocks[blk_id].borrow_addr(qb_id)

                return blk_id, qb_id

            @guppy
            @no_type_check
            def qed_policy(
                self,
                blk_ids: array[int, N] @ owned,
                op_cost: float,
            ) -> None:
                for i in blk_ids:
                    self.blocks[i].qed_counter += op_cost

                    if self.blocks[i].qed_counter >= comptime(qed_policy.threshold):
                        blk = self.take_block(i)

                        k2_primitives.qed_cycle(blk.logical_block)

                        self.put_block(i, blk)
                        self.blocks[i].qed_counter = 0.0

        # TODO: The output order of borrow is flipped with respect to borrow_more
        # for no good reason. The ordering in borrow_more is forced because
        # the op does not own the borrowed block, so it has to appear at the end.
        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._borrow")
        def _borrow(blk_id: int, qb_id: int) -> tuple[int, tuple[int, int]]:

            @guppy
            @no_type_check
            def _impl(
                state: STATE @ owned, blk_id: int, qb_id: int
            ) -> tuple[STATE, int, tuple[int, int]]:
                state.blocks[blk_id].borrow_addr(qb_id)
                return state, blk_id, (blk_id, qb_id)

            return map_global(_impl, blk_id, qb_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._borrow_more")
        def _borrow_more(blk_id: int, qb_id: int) -> tuple[tuple[int, int], int]:

            @guppy
            @no_type_check
            def _impl(
                state: STATE @ owned, blk_id: int, qb_id: int
            ) -> tuple[STATE, int, tuple[int, int]]:
                state.blocks[blk_id].borrow_addr(qb_id)
                return state, (blk_id, qb_id), blk_id

            return map_global(_impl, blk_id, qb_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._restore_some")
        def _restore_some(blk_id: int, qb_id: int) -> int:

            @guppy
            @no_type_check
            def _impl(
                state: STATE @ owned, blk_id: int, qb_id: int
            ) -> tuple[STATE, int]:
                state.blocks[blk_id].restore_addr(qb_id)
                return state, blk_id

            return map_global(_impl, blk_id, qb_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._restore")
        def _restore(blk_id: int, qb_id: int) -> int:

            @guppy
            @no_type_check
            def _impl(
                state: STATE @ owned, blk_id: int, qb_id: int
            ) -> tuple[STATE, int]:
                state.blocks[blk_id].restore_addr(qb_id)
                return state, blk_id

            return map_global(_impl, blk_id, qb_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._alloc_dynq")
        def _alloc_dynq() -> tuple[int, int]:

            @guppy
            @no_type_check
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_dyn_addr()
                return state, (blk_id, qb_id)

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._free_dynq")
        def _free_dynq(addr: tuple[int, int]) -> None:

            @guppy
            @no_type_check
            def _impl(state: STATE @ owned, addr: tuple[int, int]) -> tuple[STATE]:
                state.release_dyn_addr(addr)
                return state

            return map_global(_impl, addr)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._qed_cycle")
        def _qed_cycle(blk_id: int) -> int:

            @guppy
            @no_type_check
            def _impl(state: STATE @ owned, blk_id: int) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)

                k2_primitives.qed_cycle(blk.logical_block)

                state.put_block(blk_id, blk)
                state.blocks[blk_id].qed_counter = 0.0

                return state, blk_id

            return map_global(_impl, blk_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._prep_zero_ft")
        def _prep_zero_ft() -> int:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, int]:
                logical_block = k2_primitives.prep_zero_ft()
                blk_id = state.allocate_block(logical_block)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.prep_zero_ft))

                return state, blk_id

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._prep_y_states_non_ft")
        def _prep_y_states_non_ft() -> int:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, int]:
                logical_block = k2_primitives.prep_y_states_non_ft()
                blk_id = state.allocate_block(logical_block)

                state.qed_policy(
                    array(blk_id), comptime(qed_policy.costs.prep_y_states_non_ft)
                )

                return state, blk_id

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._prep_t_states_non_ft")
        def _prep_t_states_non_ft() -> int:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, int]:
                logical_block = k2_primitives.prep_t_states_non_ft()
                blk_id = state.allocate_block(logical_block)

                state.qed_policy(
                    array(blk_id), comptime(qed_policy.costs.prep_t_states_non_ft)
                )

                return state, blk_id

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._measure_z")
        def _measure_z(blk_id: int, qb_id: int) -> tuple[bool, int]:
            @guppy
            def _impl(
                state: STATE @ owned, blk_id: int, qb_id: int
            ) -> tuple[STATE, bool, int]:
                blk = state.take_block(blk_id)
                res = k2_primitives.measure_z(blk.logical_block, qb_id)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.measure_z))

                return state, res, blk_id

            return map_global(_impl, blk_id, qb_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._measure_z_all")
        def _measure_z_all(blk_id: int) -> array[bool, 2]:
            @guppy
            def _impl(
                state: STATE @ owned, blk_id: int
            ) -> tuple[STATE, array[bool, 2]]:
                blk = state.release_block(blk_id)
                res = k2_primitives.measure_z_all(blk.logical_block)

                state.qed_policy(
                    array(blk_id), comptime(qed_policy.costs.measure_z_all)
                )

                return state, res

            return map_global(_impl, blk_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._free")
        def _free(blk_id: int) -> None:
            @guppy
            def _impl(state: STATE @ owned, blk_id: int) -> STATE:
                state.release_block(blk_id).discard()

                return state

            return map_global(_impl, blk_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._x")
        def _x(blk_id: int, target: int) -> int:
            @guppy
            def _impl(
                state: STATE @ owned, blk_id: int, target: int
            ) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)
                k2_primitives.x(blk.logical_block, target)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.x))

                return state, blk_id

            return map_global(_impl, blk_id, target)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._z")
        def _z(blk_id: int, target: int) -> int:
            @guppy
            def _impl(
                state: STATE @ owned, blk_id: int, target: int
            ) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)
                k2_primitives.z(blk.logical_block, target)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.z))

                return state, blk_id

            return map_global(_impl, blk_id, target)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._h_all")
        def _h_all(blk_id: int) -> int:
            @guppy
            def _impl(state: STATE @ owned, blk_id: int) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)
                k2_primitives.h_all(blk.logical_block)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.h_all))

                return state, blk_id

            return map_global(_impl, blk_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._cx_intra")
        def _cx_intra(blk_id: int, target: int) -> int:
            @guppy
            def _impl(
                state: STATE @ owned, blk_id: int, target: int
            ) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)
                k2_primitives.cx_intra(blk.logical_block, target)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.cx_intra))

                return state, blk_id

            return map_global(_impl, blk_id, target)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._cx_transversal")
        def _cx_transversal(ctl_blk_id: int, tgt_blk_id: int) -> tuple[int, int]:
            @guppy
            def _impl(
                state: STATE @ owned, ctl_blk_id: int, tgt_blk_id: int
            ) -> tuple[STATE, int, int]:
                ctl_blk, tgt_blk = (
                    state.take_block(ctl_blk_id),
                    state.take_block(tgt_blk_id),
                )

                k2_primitives.cx_transversal(
                    ctl_blk.logical_block, tgt_blk.logical_block
                )

                state.put_block(ctl_blk_id, ctl_blk)
                state.put_block(tgt_blk_id, tgt_blk)

                state.qed_policy(
                    array(ctl_blk_id, tgt_blk_id),
                    comptime(qed_policy.costs.cx_transversal),
                )

                return state, ctl_blk_id, tgt_blk_id

            return map_global(_impl, ctl_blk_id, tgt_blk_id)

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._swap_intra")
        def _swap_intra(blk_id: int) -> int:
            @guppy
            def _impl(state: STATE @ owned, blk_id: int) -> tuple[STATE, int]:
                blk = state.take_block(blk_id)
                k2_primitives.swap_intra(blk.logical_block)
                state.put_block(blk_id, blk)

                state.qed_policy(array(blk_id), comptime(qed_policy.costs.swap_intra))

                return state, blk_id

            return map_global(_impl, blk_id)

        # NOTE: The following are re-implementations of what we have in
        # `guppyft.code.toy_k2.logical` for the addressable gates.
        # An alternative would be to first run a pass that replaces the
        # dynamic qubit operations with the non-primitive addressable logical
        # gates defined in that module.
        # Another alternative is to define the addressable gates in
        # `guppyft.code.toy_k2.logical` acting on the dynamic_qubit type and
        # adding HUGR extension ops to inspect these types, checking if two are
        # in the same block (which is implemented by comparing ints during
        # implement_ops), etc. In that case, we would just replace a
        # computational CX with this logical CX via the compose_op replacement,
        # and *not* have the dyn ops in the extension.

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._x_dynq")
        def _x_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            blk_id, qb_id = addr
            _x(blk_id, qb_id)
            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._z_dynq")
        def _z_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            blk_id, qb_id = addr
            _z(blk_id, qb_id)
            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._h_dynq")
        def _h_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            blk_id, qb_id = addr
            # Prepare an ancilla `|0+>` state, with the `|+>` on the index where
            # we want to apply the Hadamard.
            ancilla_blk_id = _prep_zero_ft()  # |00>
            _h_all(ancilla_blk_id)  # |++>
            # Project the other ancilla logical qubit to |0>
            if _measure_z(ancilla_blk_id, 1 - qb_id):
                _x(ancilla_blk_id, qb_id)

            # Use the ancilla state to introduce a Hadamard on the chosen index.
            # This approach follows Fig 8A from https://arxiv.org/abs/2403.16054
            # In the case where ancilla is |0>, the CX gates are cancelled and there is
            # no effect on the logical qubit at that index.
            # In the case where the ancilla is |+>, a H is applied on the block,
            # up to a Z correction if the measurement outcome is 0 and X if it is 1.
            _cx_transversal(ancilla_blk_id, blk_id)
            _h_all(ancilla_blk_id)
            _cx_transversal(blk_id, ancilla_blk_id)
            m0, m1 = _measure_z_all(ancilla_blk_id)
            m = m0 if qb_id == 0 else m1

            if m:
                _x(blk_id, qb_id)
            else:
                _z(blk_id, qb_id)
            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._cx_dynq")
        def _cx_dynq(
            ctl_addr: tuple[int, int], tgt_addr: tuple[int, int]
        ) -> tuple[tuple[int, int], tuple[int, int]]:
            ctl_blk, ctl_qb = ctl_addr
            tgt_blk, tgt_qb = tgt_addr

            # If they are the same block, we apply an intra CX
            if ctl_blk == tgt_blk:
                _cx_intra(tgt_blk, tgt_qb)

            # Otherwise, we need to decompose it
            else:
                if ctl_qb == tgt_qb:
                    _swap_intra(ctl_blk)

                _cx_transversal(ctl_blk, tgt_blk)
                _cx_intra(tgt_blk, tgt_qb)
                _cx_transversal(ctl_blk, tgt_blk)
                _cx_intra(tgt_blk, tgt_qb)

                if ctl_qb == tgt_qb:
                    _swap_intra(ctl_blk)

            return ctl_addr, tgt_addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._s_dynq")
        def _s_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            # Prepare two |Y> states
            y_blk_id = _prep_y_states_non_ft()
            # Inject only one of them
            _cx_dynq(addr, (y_blk_id, 0))
            # Measure the whole block because that's more efficient
            m0, m1 = _measure_z_all(y_blk_id)
            # But only pick the measurement outcome we care about for injection
            m = m0 if addr[1] == 0 else m1
            # Correct if necessary
            if m:
                _z_dynq(addr)

            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._sdg_dynq")
        def _sdg_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            _x_dynq(addr)
            _s_dynq(addr)
            _x_dynq(addr)
            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._t_dynq")
        def _t_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            # Prepare two T|+> states
            t_blk_id = _prep_t_states_non_ft()
            # Inject only one of them
            _cx_dynq(addr, (t_blk_id, 0))
            # Measure the whole block because that's more efficient
            m0, m1 = _measure_z_all(t_blk_id)
            # But only pick the measurement outcome we care about for injection
            m = m0 if addr[1] == 0 else m1
            # Correct if necessary
            if m:
                _s_dynq(addr)

            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._tdg_dynq")
        def _tdg_dynq(addr: tuple[int, int]) -> tuple[int, int]:
            _x_dynq(addr)
            _t_dynq(addr)
            _x_dynq(addr)
            return addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._measure_z_dynq")
        def _measure_z_dynq(addr: tuple[int, int]) -> tuple[bool, tuple[int, int]]:
            blk_id, qb_id = addr
            res, _ = _measure_z(blk_id, qb_id)
            # TODO: For the sake of consistency with Guppy, measure_z_dyn
            # should *not* return the dynamic qubit. Instead, it should be
            # reset to zero and released, so that it can be picked up again
            # by `allocate_dynq_addr`. Currently, this requires changing
            # the signature of the HUGR op.
            # state.release_dyn_addr(addr)
            return res, addr

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._no_op_decode1")
        def _no_op_decode1(outcome: bool) -> bool:
            # In the current version of ToyK2, decoding actually happens within
            # the implementation of the measure primitive, which returns bool.
            # Hence, this operation is just a no-op to replace the computational
            # `read()` with.
            return outcome

        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2._no_op_decode2")
        def _no_op_decode2(outcome: array[bool, 2]) -> array[bool, 2]:
            # Same as _no_op_decode1, but for the outcome of `measure_z_all`.
            return outcome

        @guppy.declare
        @no_type_check
        @link_name("guppyft.toy_k2.gen_state")
        def state_gen_decl() -> STATE: ...
        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2.gen_state")
        def state_gen() -> STATE:
            return STATE(
                array(nothing[RuntimeBlock]() for _ in range(comptime(n_blocks))),
                Stack(
                    array(some(blk_id) for blk_id in range(comptime(n_blocks))),
                    comptime(n_blocks),
                ),
                empty_stack(),
            )

        @guppy.declare
        @no_type_check
        @link_name("guppyft.toy_k2.discard_state")
        def state_discard_decl(state: "STATE" @ owned) -> None: ...
        @guppy
        @no_type_check
        @link_name("guppyft.toy_k2.discard_state")
        def state_discard(state: "STATE" @ owned) -> None:
            for blk in state.blocks:
                if blk.is_some():
                    blk.unwrap().discard()
                else:
                    blk.unwrap_nothing()

        def build_wrapper(
            func: GuppyFunctionDefinition[[], None],
        ) -> GuppyFunctionDefinition[[], None]:
            @guppy
            @no_type_check
            def wrapper() -> None:
                state = state_gen_decl()
                state = with_global(state, func)
                state_discard_decl(state)

            return wrapper  # type: ignore[no-any-return]

        lib = GuppyLibrary.from_members(
            state_gen,
            state_discard,
            _borrow,
            _borrow_more,
            _restore_some,
            _restore,
            _alloc_dynq,
            _free_dynq,
            _qed_cycle,
            _prep_zero_ft,
            _prep_y_states_non_ft,
            _prep_t_states_non_ft,
            _measure_z,
            _measure_z_all,
            _free,
            _x,
            _z,
            _h_all,
            _cx_intra,
            _cx_transversal,
            _swap_intra,
            _x_dynq,
            _z_dynq,
            _h_dynq,
            _cx_dynq,
            _s_dynq,
            _sdg_dynq,
            _t_dynq,
            _tdg_dynq,
            _measure_z_dynq,
            _no_op_decode1,
            _no_op_decode2,
        ).compile()

        ops = OpReplacements().with_generated_decls(
            {
                ("guppyft.toy_k2.ops", "borrow"): "guppyft.toy_k2._borrow",
                ("guppyft.toy_k2.ops", "borrow_more"): "guppyft.toy_k2._borrow_more",
                ("guppyft.toy_k2.ops", "restore_some"): "guppyft.toy_k2._restore_some",
                ("guppyft.toy_k2.ops", "restore"): "guppyft.toy_k2._restore",
                ("guppyft.toy_k2.ops", "alloc_dynq"): "guppyft.toy_k2._alloc_dynq",
                ("guppyft.toy_k2.ops", "free_dynq"): "guppyft.toy_k2._free_dynq",
                ("guppyft.toy_k2.ops", "qed_cycle"): "guppyft.toy_k2._qed_cycle",
                ("guppyft.toy_k2.ops", "prep_zero_ft"): "guppyft.toy_k2._prep_zero_ft",
                (
                    "guppyft.toy_k2.ops",
                    "prep_y_states_non_ft",
                ): "guppyft.toy_k2._prep_y_states_non_ft",
                (
                    "guppyft.toy_k2.ops",
                    "prep_t_states_non_ft",
                ): "guppyft.toy_k2._prep_t_states_non_ft",
                ("guppyft.toy_k2.ops", "measure_z"): "guppyft.toy_k2._measure_z",
                (
                    "guppyft.toy_k2.ops",
                    "measure_z_all",
                ): "guppyft.toy_k2._measure_z_all",
                ("guppyft.toy_k2.ops", "free"): "guppyft.toy_k2._free",
                ("guppyft.toy_k2.ops", "x"): "guppyft.toy_k2._x",
                ("guppyft.toy_k2.ops", "z"): "guppyft.toy_k2._z",
                ("guppyft.toy_k2.ops", "h_all"): "guppyft.toy_k2._h_all",
                ("guppyft.toy_k2.ops", "cx_intra"): "guppyft.toy_k2._cx_intra",
                (
                    "guppyft.toy_k2.ops",
                    "cx_transversal",
                ): "guppyft.toy_k2._cx_transversal",
                ("guppyft.toy_k2.ops", "swap_intra"): "guppyft.toy_k2._swap_intra",
                ("guppyft.toy_k2.ops", "x_dynq"): "guppyft.toy_k2._x_dynq",
                ("guppyft.toy_k2.ops", "z_dynq"): "guppyft.toy_k2._z_dynq",
                ("guppyft.toy_k2.ops", "h_dynq"): "guppyft.toy_k2._h_dynq",
                ("guppyft.toy_k2.ops", "cx_dynq"): "guppyft.toy_k2._cx_dynq",
                ("guppyft.toy_k2.ops", "s_dynq"): "guppyft.toy_k2._s_dynq",
                ("guppyft.toy_k2.ops", "sdg_dynq"): "guppyft.toy_k2._sdg_dynq",
                ("guppyft.toy_k2.ops", "t_dynq"): "guppyft.toy_k2._t_dynq",
                ("guppyft.toy_k2.ops", "tdg_dynq"): "guppyft.toy_k2._tdg_dynq",
                (
                    "guppyft.toy_k2.ops",
                    "measure_z_dynq",
                ): "guppyft.toy_k2._measure_z_dynq",
                (
                    "guppyft.toy_k2.ops",
                    "decode_qubit_measurement",
                ): "guppyft.toy_k2._no_op_decode1",
                (
                    "guppyft.toy_k2.ops",
                    "decode_block_measurement",
                ): "guppyft.toy_k2._no_op_decode2",
            }
        )
        tys = TyReplacements().with_types(
            [
                ("guppyft.toy_k2.types", "block"),
                ("guppyft.toy_k2.types", "borrowed_block"),
                ("guppyft.toy_k2.types", "dynamic_qubit"),
                ("guppyft.toy_k2.types", "block_measurement"),
                ("guppyft.toy_k2.types", "qubit_measurement"),
            ]
        )

        return ImplementOpsSpec(
            ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib]
        )

    def _gen_encoder_spec(self, n_blocks: int) -> EncodeSpec:
        """Generate the full `EncoderSpec` (logical encoding + op implementations)
        for a program using `n_blocks` logical blocks."""
        impl_spec = self._gen_implement_spec(n_blocks)

        ext = ExtensionRegistry.from_extensions(
            [toy_k2_ops(), toy_k2_types(), std_ops(), std_types()]
        )
        # `_std_extensions` should not be necessary but seems to be
        #  required for `borrow_array` when (de)serializing.
        ext.extend(_std_extensions())

        logical_compiler = ReplacementCompiler(
            op_replacements={
                ("tket.quantum", "QAlloc"): ("guppyft.toy_k2.ops", "alloc_dynq", []),
                ("tket.quantum", "MeasureFree"): (
                    # TODO: this will fail due to signature mismatch,
                    # see comment in _measure_z_dynq
                    "guppyft.toy_k2.ops",
                    "measure_z_dynq",
                    [],
                ),
                ("tket.quantum", "QFree"): ("guppyft.toy_k2.ops", "free_dynq", []),
                ("tket.measurement", "Read"): (
                    "guppyft.toy_k2.ops",
                    "decode_qubit_type",
                    [],
                ),
                ("tket.quantum", "X"): ("guppyft.toy_k2.ops", "x_dynq", []),
                ("tket.quantum", "Z"): ("guppyft.toy_k2.ops", "z_dynq", []),
                ("tket.quantum", "H"): ("guppyft.toy_k2.ops", "h_dynq", []),
                ("tket.quantum", "S"): ("guppyft.toy_k2.ops", "s_dynq", []),
                ("tket.quantum", "Sdg"): ("guppyft.toy_k2.ops", "sdg_dynq", []),
                ("tket.quantum", "T"): ("guppyft.toy_k2.ops", "t_dynq", []),
                ("tket.quantum", "Tdg"): ("guppyft.toy_k2.ops", "tdg_dynq", []),
                ("tket.quantum", "CX"): ("guppyft.toy_k2.ops", "cx_dynq", []),
            },
            compound_op_replacements={},
            ty_replacements={
                ("prelude", "qubit"): ("guppyft.toy_k2.types", "dynamic_qubit"),
                ("tket.measurement", "Measurement"): (
                    "guppyft.toy_k2.types",
                    "qubit_measurement",
                ),
            },
            extensions=ext,
        )

        return EncodeSpec(
            compile=logical_compiler, implement_ops=ImplementOps.for_spec(impl_spec)
        )

    def with_qed_policy(self, qed_policy: QEDPolicy) -> Self:
        """Set the QED policy."""
        return replace(self, _qed_policy=qed_policy)

    def build(self, n_blocks: int) -> ToyK2Instance:
        """Build a `ToyK2Instance` configured for `n_blocks` logical blocks."""
        encoder_spec = self._gen_encoder_spec(n_blocks)
        return ToyK2Instance(_spec=encoder_spec)
