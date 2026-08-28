from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Self, cast, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder, EmulatorInstance
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.collections import Stack, empty_queue
from guppylang.std.option import Option, nothing, some
from guppylang.std.platform import panic
from hugr.ext import ExtensionRegistry
from hugr.package import Package
from hugr.std import _std_extensions

from guppyft.code._state_factory import StateFactory
from guppyft.code.steane.primitives import (
    cx,
    decode,
    h,
    inject_magic_for_t,
    inject_magic_for_tdg,
    knill_qec_cycle,
    measure_z,
    prep_t_state_ft,
    prep_zero_ft,
    s,
    sdg,
    steane_x_qec_cycle,
    steane_z_qec_cycle,
    x,
    y,
    z,
)
from guppyft.code.util import LogicalBlock, RawMeasurement
from guppyft.encode import (
    EncoderParams,
    EncoderSpec,
    ImplementOpsSpec,
    OpReplacements,
    ReplaceEncoder,
    TyReplacements,
    encode,
    implement_ops,
)
from guppyft.extensions import std_ops, std_types, steane_ops, steane_types
from guppyft.globals import map_global, with_global
from guppyft.logical import steane as steane_logical

N = guppy.nat_var("N")


@dataclass(frozen=True, kw_only=True)
class SteaneEncoderParams(EncoderParams):
    n_blocks: int

    def encoding(self) -> str:
        return "steane"

    def params(self) -> Mapping[str, Any]:
        return {"n_blocks": self.n_blocks}


@dataclass(frozen=True)
class RUSStateFactoryConf:
    """Steane RUS state factory configuration.

    Attributes:
        size: Maximum number of states to be produced in parallel.
        max_attempts: Maximum number of repeat-until-success attempts.
    """

    size: int
    max_attempts: int


@dataclass(frozen=True, kw_only=True)
class _SteaneFactoryConf:
    """Configuration for each of the Steane state factories."""

    zero: RUSStateFactoryConf = field(default_factory=lambda: RUSStateFactoryConf(1, 5))
    magic: RUSStateFactoryConf = field(
        default_factory=lambda: RUSStateFactoryConf(1, 5)
    )


class QECStyle(Enum):
    """The style of syndrome extraction to use during a QEC cycle."""

    Knill = auto()
    Steane = auto()


@dataclass
class QECPolicy:
    """Policy to determine when QEC cycles are injected.

    Each logical block accumulates a cost based on `costs`. Once a
    block's accumulated cost reaches `threshold`, a QEC cycle of the given
    `style` is performed on that block and its counter is reset.

    Attributes:
        style: The style of syndrome extraction to use (see `QECStyle`).
        threshold: Threshold at which a QEC cycle is triggered.
        costs: Mapping from operation name to its cost.
               Defaults to 0 for any op not explicitly set.
    """

    style: QECStyle = QECStyle.Steane
    threshold: int = 1
    costs: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def set_cost(self, op: str, cost: float) -> None:
        """Set the cost of an operation.

        Args:
            op: Name of the operation.
            cost: Non-negative cost to assign to the operation.
        """
        if cost < 0:
            raise ValueError(f"Op cost cannot be negative: received {cost}")
        self.costs[op] = cost


@dataclass(frozen=True)
class SteaneInstance:
    """A Steane architecture instance built by `SteaneBuilder.build`."""

    _spec: EncoderSpec

    def encode(self, pkg: Package) -> Package:
        """Encode a computational package with the Steane instance."""
        self.check_encoding(pkg)
        return encode(pkg, self._spec)

    def implement_ops(self, pkg: Package) -> Package:
        """Implement logical ops in `pkg` using this instance's op implementations."""
        return implement_ops(pkg, self._spec.implement_spec)

    def check_encoding(self, hugr: Package) -> None:
        """Check that a HUGR package can be encoded.

        Note: this test is limited to the `tket.quantum` extension.
        """
        encoder_pass = cast("ReplaceEncoder", self._spec.to_logical)

        for node, data in hugr.modules[0].nodes():
            op_qual_name = data.op.name()
            if "tket.quantum" in op_qual_name:
                op_name = op_qual_name.split(".")[-1]

                if ("tket.quantum", op_name) not in encoder_pass.op_replacements:
                    raise ValueError(
                        f"Error encoding `{op_qual_name}` at node {node}. "
                        "Operation not yet supported during encoding."
                    )

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
        encoded_pkg = self.encode(pkg)
        if builder is None:
            builder = EmulatorBuilder()

        emulator = builder.build(encoded_pkg, n_qubits)

        return emulator


@dataclass(frozen=True, kw_only=True)
class SteaneBuilder:
    """Steane architecture builder class for creating `SteaneInstance` objects."""

    _factory_confs: _SteaneFactoryConf = field(default_factory=_SteaneFactoryConf)
    _qec_policy: QECPolicy = field(default_factory=QECPolicy)

    def _gen_implement_spec(self, n_blocks: int) -> ImplementOpsSpec:
        """Generate the `ImplementOpsSpec` providing Steane implementations of
        logical ops for a program using `n_blocks` logical blocks."""

        qec_policy = self._qec_policy

        # TODO STATE should be generic for all codes. The methods that are code specific
        # should be `@guppy.declare` and each code can provide an implementation to be
        # linked i.e. `allocate_next_addr`.
        # See https://github.com/quantinuum-dev/guppyft/issues/179
        @guppy.struct
        class STATE:
            blocks: array[Option[LogicalBlock[7]], comptime(n_blocks)]  # type: ignore[valid-type,type-arg]
            addr_stack: Stack[tuple[int, int], comptime(n_blocks)]  # type: ignore[valid-type,type-arg]
            qec_counter: array[float, comptime(n_blocks)]  # type: ignore[valid-type]

            zero_state_factory: StateFactory[  # type: ignore[valid-type,type-arg]
                7, 1, comptime(self._factory_confs.zero.size)
            ]
            magic_state_factory: StateFactory[  # type: ignore[valid-type,type-arg]
                7, 8, comptime(self._factory_confs.magic.size)
            ]

            @guppy
            @no_type_check
            def take_block(self, blk_id: int) -> LogicalBlock[7]:
                return self.blocks[blk_id].take().unwrap()

            @guppy
            @no_type_check
            def put_block(self, blk_id: int, blk: LogicalBlock[7] @ owned) -> None:
                self.blocks[blk_id].swap(some(blk)).unwrap_nothing()

            @guppy
            @no_type_check
            def free_addr(self, addr: tuple[int, int]) -> None:
                self.addr_stack.push(addr)

            @guppy
            @no_type_check
            def allocate_next_addr(self: "STATE") -> tuple[int, int]:
                if len(self.addr_stack) == 0:
                    exit("allocate_next_addr: No more logical qubits to allocate")
                next_addr = self.addr_stack.pop()

                blk = self.blocks[next_addr[0]].take()

                if blk.is_some():
                    # Since Steane is k=1, blocks are either not allocated, or
                    # completely filled, so this should never happen.
                    panic("allocate_next_addr: Next block was not nothing.")

                self.blocks[next_addr[0]].swap(blk).unwrap_nothing()

                # Reset qec_counter for block
                self.qec_counter[next_addr[0]] = 0.0

                return next_addr

            @guppy
            @no_type_check
            def qec_policy(
                self,
                blk_ids: array[int, N] @ owned,
                op_cost: float,
            ) -> None:
                for i in blk_ids:
                    self.qec_counter[i] = self.qec_counter[i] + op_cost

                    if self.qec_counter[i] >= comptime(qec_policy.threshold):
                        blk = self.take_block(i)

                        qec_cycle_def(self, blk)

                        self.put_block(i, blk)
                        self.qec_counter[i] = 0.0

        match qec_policy.style:
            case QECStyle.Knill:

                @guppy
                @no_type_check
                def qec_cycle_def(state: STATE, q: LogicalBlock[7]) -> None:
                    # Allocate new blocks for the Bell state
                    ancilla0 = state.zero_state_factory.get_state()
                    ancilla1 = state.zero_state_factory.get_state()
                    knill_qec_cycle(q, ancilla0, ancilla1)

            case QECStyle.Steane:

                @guppy
                @no_type_check
                def qec_cycle_def(state: STATE, q: LogicalBlock[7]) -> None:
                    ancillaX = state.zero_state_factory.get_state()
                    steane_x_qec_cycle(q, ancillaX)
                    ancillaZ = state.zero_state_factory.get_state()
                    steane_z_qec_cycle(q, ancillaZ)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._qec_cycle")
        def _qec_cycle(q: tuple[int, int]) -> tuple[tuple[int, int]]:

            @guppy
            @no_type_check
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)

                qec_cycle_def(state, blk)

                state.put_block(blk_id, blk)
                state.qec_counter[blk_id] = 0.0

                return state, q

            return (q,)

        # TODO Defining the primitives to use the global state requires
        # a lot of "boilerplate" code. We should provide helper methods
        # to easily define these functions from the primitives. I think
        # this could be replaced with `@custom_function` and a custom
        # compiler.
        # See https://github.com/quantinuum-dev/guppyft/issues/161.
        @guppy
        @no_type_check
        @link_name("guppyft.steane._prep_zero")
        def _prep_zero() -> tuple[tuple[int, int]]:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_next_addr()
                blk = state.zero_state_factory.get_state()
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Prep_zero"]))

                return state, (blk_id, qb_id)

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._prep_magic_for_t_like")
        def _prep_magic_for_t_like() -> tuple[tuple[int, int]]:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_next_addr()
                blk = state.magic_state_factory.get_state()
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Prep_T"]))

                return state, (blk_id, qb_id)

            return map_global(_impl)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._measure_z")
        def _measure_z(q: tuple[int, int]) -> RawMeasurement[7]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, RawMeasurement[7]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)

                res = measure_z(blk)

                state.free_addr(q)
                return state, res

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._free")
        def _free(q: tuple[int, int]) -> None:
            @guppy
            def _impl(state: STATE @ owned, q: tuple[int, int]) -> STATE:
                blk_id, _ = q
                blk = state.take_block(blk_id)

                blk.discard()

                state.free_addr(q)
                return state

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._x")
        def _x(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                x(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["X"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._y")
        def _y(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                y(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Y"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._z")
        def _z(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                z(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Z"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._h")
        def _h(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                h(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["H"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._s")
        def _s(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                s(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["S"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._sdg")
        def _sdg(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                sdg(blk)
                state.put_block(blk_id, blk)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Sdg"]))

                return state, q

            return map_global(_impl, q)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._inject_magic_for_t")
        def _inject_magic_for_t(
            q: tuple[int, int], a: tuple[int, int]
        ) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int], a: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                resource = state.take_block(a[0])
                inject_magic_for_t(blk, resource)
                state.put_block(blk_id, blk)
                state.free_addr(a)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs["Inject_T"]))

                return state, q

            return map_global(_impl, q, a)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._inject_magic_for_tdg")
        def _inject_magic_for_tdg(
            q: tuple[int, int], a: tuple[int, int]
        ) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int], a: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.take_block(blk_id)
                resource = state.take_block(a[0])
                inject_magic_for_tdg(blk, resource)
                state.put_block(blk_id, blk)
                state.free_addr(a)

                state.qec_policy(
                    array(blk_id), comptime(qec_policy.costs["Inject_Tdg"])
                )

                return state, q

            return map_global(_impl, q, a)

        @guppy
        @no_type_check
        @link_name("guppyft.steane._cx")
        def _cx(
            ctl: tuple[int, int], tgt: tuple[int, int]
        ) -> tuple[tuple[int, int], tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, ctl: tuple[int, int], tgt: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int], tuple[int, int]]:
                ctl_blk, tgt_blk = state.take_block(ctl[0]), state.take_block(tgt[0])

                cx(ctl_blk, tgt_blk)

                state.put_block(ctl[0], ctl_blk)
                state.put_block(tgt[0], tgt_blk)

                state.qec_policy(
                    array(ctl[0], tgt[0]), comptime(qec_policy.costs["CX"])
                )

                return state, ctl, tgt

            return map_global(_impl, ctl, tgt)

        @guppy.declare
        @no_type_check
        @link_name("guppyft.steane.gen_state")
        def state_gen_decl() -> STATE: ...
        @guppy
        @no_type_check
        @link_name("guppyft.steane.gen_state")
        def state_gen() -> STATE:
            return STATE(
                array(nothing[LogicalBlock[7]]() for _ in range(comptime(n_blocks))),
                Stack(
                    array(some((blk, 1)) for blk in range(comptime(n_blocks))),
                    comptime(n_blocks),
                ),
                # qec_counter
                array(0.0 for _ in range(comptime(n_blocks))),
                # Zero state factory
                StateFactory(
                    prep_zero_ft,
                    comptime(self._factory_confs.zero.max_attempts),
                    empty_queue(),
                ),
                # Magic state factory
                StateFactory(
                    prep_t_state_ft,
                    comptime(self._factory_confs.magic.max_attempts),
                    empty_queue(),
                ),
            )

        @guppy.declare
        @no_type_check
        @link_name("guppyft.steane.discard_state")
        def state_discard_decl(state: "STATE" @ owned) -> None: ...
        @guppy
        @no_type_check
        @link_name("guppyft.steane.discard_state")
        def state_discard(state: "STATE" @ owned) -> None:
            for blk in state.blocks:
                if blk.is_some():
                    blk.unwrap().discard()
                else:
                    blk.unwrap_nothing()

            state.zero_state_factory.discard()
            state.magic_state_factory.discard()

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
            _qec_cycle,
            _prep_zero,
            _prep_magic_for_t_like,
            _measure_z,
            _free,
            decode,
            _x,
            _y,
            _z,
            _h,
            _s,
            _sdg,
            _inject_magic_for_t,
            _inject_magic_for_tdg,
            _cx,
        ).compile()

        ops = OpReplacements().with_generated_decls(
            {
                ("guppyft.steane.ops", "prep_zero"): "guppyft.steane._prep_zero",
                ("guppyft.steane.ops", "measure_z"): "guppyft.steane._measure_z",
                ("guppyft.steane.ops", "qec_cycle"): "guppyft.steane._qec_cycle",
                ("guppyft.steane.ops", "free"): "guppyft.steane._free",
                ("guppyft.steane.ops", "x"): "guppyft.steane._x",
                ("guppyft.steane.ops", "y"): "guppyft.steane._y",
                ("guppyft.steane.ops", "z"): "guppyft.steane._z",
                ("guppyft.steane.ops", "h"): "guppyft.steane._h",
                ("guppyft.steane.ops", "s"): "guppyft.steane._s",
                ("guppyft.steane.ops", "sdg"): "guppyft.steane._sdg",
                (
                    "guppyft.steane.ops",
                    "prep_magic_for_t_like",
                ): "guppyft.steane._prep_magic_for_t_like",
                (
                    "guppyft.steane.ops",
                    "inject_magic_for_t",
                ): "guppyft.steane._inject_magic_for_t",
                (
                    "guppyft.steane.ops",
                    "inject_magic_for_tdg",
                ): "guppyft.steane._inject_magic_for_tdg",
                ("guppyft.steane.ops", "cx"): "guppyft.steane._cx",
                ("guppyft.steane.ops", "decode"): "guppyft.steane.decode",
            }
        )
        tys = TyReplacements().with_types(
            [
                ("guppyft.steane.types", "qubit"),
                ("guppyft.steane.types", "measurement"),
            ]
        )

        return ImplementOpsSpec(
            ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib]
        )

    def _gen_encoder_spec(self, n_blocks: int) -> EncoderSpec:
        """Generate the full `EncoderSpec` (logical encoding + op implementations)
        for a program using `n_blocks` logical blocks."""

        impl_spec = self._gen_implement_spec(n_blocks)

        ext = ExtensionRegistry.from_extensions(
            [steane_ops(), steane_types(), std_ops(), std_types()]
        )
        # `_std_extensions` should not be necessary but seems to be
        #  required for `borrow_array` when (de)serialising.
        ext.extend(_std_extensions())

        std_encoder = ReplaceEncoder(
            op_replacements={
                ("tket.quantum", "QAlloc"): ("guppyft.steane.ops", "prep_zero", []),
                ("tket.quantum", "MeasureFree"): (
                    "guppyft.steane.ops",
                    "measure_z",
                    [],
                ),
                ("tket.quantum", "QFree"): ("guppyft.steane.ops", "free", []),
                ("tket.measurement", "Read"): ("guppyft.steane.ops", "decode", []),
                ("tket.quantum", "X"): ("guppyft.steane.ops", "x", []),
                ("tket.quantum", "Y"): ("guppyft.steane.ops", "y", []),
                ("tket.quantum", "Z"): ("guppyft.steane.ops", "z", []),
                ("tket.quantum", "H"): ("guppyft.steane.ops", "h", []),
                ("tket.quantum", "S"): ("guppyft.steane.ops", "s", []),
                ("tket.quantum", "Sdg"): ("guppyft.steane.ops", "sdg", []),
                ("tket.quantum", "CX"): ("guppyft.steane.ops", "cx", []),
            },
            compound_op_replacements={
                ("tket.quantum", "T"): steane_logical.t,
                ("tket.quantum", "Tdg"): steane_logical.tdg,
            },
            ty_replacements={
                ("prelude", "qubit"): ("guppyft.steane.types", "qubit"),
                ("tket.measurement", "Measurement"): (
                    "guppyft.steane.types",
                    "measurement",
                ),
            },
            extensions=ext,
        )

        return EncoderSpec(to_logical=std_encoder, implement_spec=impl_spec)

    def with_qec_policy(self, qec_policy: QECPolicy) -> Self:
        """Set the QEC policy."""
        return replace(self, _qec_policy=qec_policy)

    def with_zero_factory_conf(self, conf: RUSStateFactoryConf) -> Self:
        """Set the zero state factory configuration."""
        return replace(
            self,
            _factory_confs=replace(self._factory_confs, zero=conf),
        )

    def with_magic_factory_conf(self, conf: RUSStateFactoryConf) -> Self:
        """Set the magic state factory configuration."""
        return replace(
            self,
            _factory_confs=replace(self._factory_confs, magic=conf),
        )

    def build(self, n_blocks: int) -> SteaneInstance:
        """Build a `SteaneInstance` configured for `n_blocks` logical blocks."""
        encoder_spec = self._gen_encoder_spec(n_blocks)
        return SteaneInstance(_spec=encoder_spec)
