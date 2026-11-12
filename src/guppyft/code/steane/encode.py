"""Builder and encoding implementation for the Steane QEC architecture."""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum, auto
from typing import Any, Self, no_type_check

from guppylang import guppy
from guppylang.decorator import custom_guppy_decorator
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.array import empty_array
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.collections import Stack, empty_queue
from guppylang.std.option import some
from guppylang.std.platform import panic
from hugr import Hugr
from hugr.ext import ExtensionRegistry, OpDef
from hugr.package import Package
from hugr.std import _std_extensions
from hugr.utils import JsonType
from tket_exts import rotation

from guppyft._util import PathDict
from guppyft.code.steane.primitives import (
    cx,
    cz,
    decode,
    h,
    inject_t,
    inject_tdg,
    knill_qec_cycle,
    measure_z,
    prep_t_state_ft,
    prep_zero_ft,
    reichardt_qec_cycle,
    s,
    sdg,
    steane_x_qec_cycle,
    steane_z_qec_cycle,
    x,
    y,
    z,
)
from guppyft.encode import (
    AnnotatingArchitectureInstance,
    EncodeSpec,
    EncodingArchitectureInstance,
    ImplementOps,
    ImplementOpsSpec,
    OpReplacements,
    ReplacementCompiler,
    TyReplacements,
    annotate_encoding,
    encode,
)
from guppyft.extensions import std_ops, std_types, steane_ops, steane_types
from guppyft.globals import map_global, with_global
from guppyft.std import LogicalBlock
from guppyft.std.state_factory import StateFactory

from . import logical as steane_logical
from .primitives import RawMeasurement

_SCHEMA_VERSION = 1

N = guppy.nat_var("N")


@dataclass(frozen=True)
class RUSStateFactoryConf:
    """Steane RUS state factory configuration.

    Attributes:
        size: Maximum number of states to be produced in parallel.
        max_attempts: Maximum number of repeat-until-success attempts.
    """

    size: int
    max_attempts: int

    def to_json(self) -> JsonType:
        """Serialize the RUS state factory config to JSON."""
        return asdict(self)

    @classmethod
    def from_json(
        cls, values: dict[str, Any], *, defaults_from: "RUSStateFactoryConf"
    ) -> "RUSStateFactoryConf":
        """Deserialize the RUS state factory config from JSON."""
        return cls(
            size=values["size"]
            if values.get("size") is not None
            else defaults_from.size,
            max_attempts=values["max_attempts"]
            if values.get("max_attempts") is not None
            else defaults_from.max_attempts,
        )


class QECStyle(StrEnum):
    """The style of syndrome extraction to use during a QEC cycle."""

    Knill = auto()
    Steane = auto()
    Reichardt = auto()


@dataclass
class QECPolicy:
    """Policy to determine when QEC cycles are injected.

    Each logical block accumulates a cost based on `costs`. Once a
    block's accumulated cost reaches `threshold`, a QEC cycle of the given
    `style` is performed on that block and its counter is reset.

    Attributes:
        style: The style of syndrome extraction to use (see `QECStyle`).
        threshold: Threshold at which a QEC cycle is triggered.
        costs: See `QECPolicy.OperationCosts`.
    """

    @dataclass
    class OperationCosts:
        """Configuration for operation costs. Used e.g. for applying QEC cycles."""

        prep_zero: float = 0.0
        prep_t: float = 0.0
        x: float = 0.0
        y: float = 0.0
        z: float = 0.0
        h: float = 0.0
        s: float = 0.0
        sdg: float = 0.0
        inject_t: float = 0.0
        inject_tdg: float = 0.0
        cx: float = 0.0
        cz: float = 0.0

        def __setattr__(self, key: str, value: float) -> None:
            """Set a non-negative cost for a known logical operation."""
            if not hasattr(self, key):
                raise KeyError(f"Unknown cost key: {key}")
            if value < 0:
                raise ValueError(f"Op cost cannot be negative: received {value}")
            super().__setattr__(key, value)

    style: QECStyle = QECStyle.Steane
    threshold: int = 1
    costs: OperationCosts = field(default_factory=OperationCosts)

    def to_json(self) -> JsonType:
        """Serialize the QEC policy to JSON."""
        return asdict(self)

    @classmethod
    def from_json(cls, values: dict[str, Any]) -> "QECPolicy":
        """Deserialize the QEC policy from JSON."""
        costs = QECPolicy.OperationCosts(**values.get("costs", {}))
        policy = cls(costs=costs)
        if (style := values.get("style")) is not None:
            policy.style = QECStyle(style)
        if (threshold := values.get("threshold")) is not None:
            policy.threshold = threshold
        return policy


@dataclass(frozen=True, kw_only=True)
class _SteaneOptions:
    zero_factory_conf: RUSStateFactoryConf
    magic_factory_conf: RUSStateFactoryConf
    qec_policy: QECPolicy


@dataclass(frozen=True)
class SteaneInstance(AnnotatingArchitectureInstance, EncodingArchitectureInstance):
    """A Steane architecture instance built by `SteaneBuilder.build`."""

    _spec: EncodeSpec = field(compare=False)
    _n_blocks: int

    _options: _SteaneOptions

    def annotate(self, hugr: Package | Hugr[Any]) -> None:
        """Annotate the current parameters of the Steane code architecture on the given
        HUGR in metadata. See `guppyft.encode.annotate` for more information."""
        annotate_encoding(
            hugr,
            "steane",
            {
                "schema_version": _SCHEMA_VERSION,
                "n_blocks": self._n_blocks,
                "zero_factory": self._options.zero_factory_conf.to_json(),
                "magic_factory": self._options.magic_factory_conf.to_json(),
                "qec_policy": self._options.qec_policy.to_json(),
            },
        )

    def _encode(self, pkg: Package, *, as_bytes: bool) -> Package | bytes:
        self.check_may_encode(pkg)
        pkg_bytes: Package | bytes = encode(pkg, self._spec, as_bytes=as_bytes)
        return pkg_bytes

    def compile(self, pkg: Package) -> Package:
        """Compile a computational package to logical with the Steane instance."""
        self.check_may_encode(pkg)
        assert self._spec.compile is not None
        return self._spec.compile(pkg)

    def _implement_ops(self, pkg: Package, *, as_bytes: bool) -> Package | bytes:
        assert self._spec.implement_ops is not None
        pkg_bytes: Package | bytes = self._spec.implement_ops(pkg, as_bytes=as_bytes)
        return pkg_bytes

    def check_may_encode(self, hugr: Package) -> None:
        """Check whether any issues can be detected that would arise when trying to
        encode the given package, e.g. the package containing unsupported gates.

        Note that this function returning without error is not a guarantee that a
        subsequent call to `encode` will succeed."""
        assert self._spec.compile is not None
        if (error := self._spec.compile.check_may_compile(hugr)) is not None:
            raise error


@dataclass(frozen=True, kw_only=True)
class SteaneBuilder:
    """Steane architecture builder class for creating `SteaneInstance` objects."""

    _options: _SteaneOptions = field(
        default_factory=lambda: _SteaneOptions(
            zero_factory_conf=RUSStateFactoryConf(1, 5),
            magic_factory_conf=RUSStateFactoryConf(1, 5),
            qec_policy=QECPolicy(),
        )
    )

    def _gen_implement_spec(self, n_blocks: int) -> ImplementOpsSpec:
        """Generate the `ImplementOpsSpec` providing Steane implementations of
        logical ops for a program using `n_blocks` logical blocks."""
        qec_policy = self._options.qec_policy

        lib = GuppyLibrary(members=[])
        ops = OpReplacements()

        def _register_op_replacement(
            op_def: OpDef,
        ) -> Callable[[Callable[..., Any]], GuppyFunctionDefinition[Any, Any]]:
            @custom_guppy_decorator
            def decorator(
                func: Callable[..., Any],
            ) -> GuppyFunctionDefinition[Any, Any]:
                # Generate guppy function
                name = f"link.{op_def.qualified_name()}"
                guppy_func = guppy(link_name(name)(func))

                # Register in library and for op replacement
                lib.register_member(guppy_func)
                ops.with_generated_decl(op_def, name)

                return guppy_func

            return decorator

        # TODO STATE should be generic for all codes. The methods that are code specific
        # should be `@guppy.declare` and each code can provide an implementation to be
        # linked i.e. `allocate_next_addr`.
        # See https://github.com/Quantinuum/guppyft/issues/179
        @guppy.struct
        class STATE:
            blocks: array[LogicalBlock[7], n_blocks]  # type: ignore[valid-type,type-arg]
            addr_stack: Stack[tuple[int, int], n_blocks]  # type: ignore[valid-type]
            qec_counter: array[float, n_blocks]  # type: ignore[valid-type]
            # Blocks held by the program or gadgets, excluding factory queues
            data_block_count: int

            zero_state_factory: StateFactory[  # type: ignore[type-arg]
                7, 1, comptime(self._options.zero_factory_conf.size)  # type: ignore[valid-type]
            ]
            magic_state_factory: StateFactory[  # type: ignore[type-arg]
                7, 8, comptime(self._options.magic_factory_conf.size)  # type: ignore[valid-type]
            ]

            @guppy
            def free_blocks(self) -> int:
                return (
                    n_blocks
                    - self.data_block_count
                    - len(self.zero_state_factory.batch)
                    - len(self.magic_state_factory.batch)
                )

            @guppy
            @no_type_check
            def get_zero_state(self) -> LogicalBlock[7]:
                # TODO Reclaim surplus candidates from the other factory when needed.
                limit = self.free_blocks() + len(self.zero_state_factory.batch)
                blk = self.zero_state_factory.get_state_with_batch_size_limit(limit)
                self.data_block_count += 1
                return blk

            @guppy
            @no_type_check
            def get_magic_state(self) -> LogicalBlock[7]:
                limit = self.free_blocks() + len(self.magic_state_factory.batch)
                blk = self.magic_state_factory.get_state_with_batch_size_limit(limit)
                self.data_block_count += 1
                return blk

            @guppy
            @no_type_check
            def with_zero_states(
                self,
                q: LogicalBlock[7],
                gadget: Callable[
                    [LogicalBlock[7], array[LogicalBlock[7], N] @ owned], None
                ],
            ) -> None:
                """Helper method to call QEC gadgets that require zero states
                as input. This allows the number of available blocks to be managed
                by `STATE`."""
                if self.free_blocks() + len(self.zero_state_factory.batch) < N:
                    exit("with_zero_states: not enough blocks for gadget")
                zero_states = array(self.get_zero_state() for _ in range(N))
                gadget(q, zero_states)
                self.data_block_count -= N

            @guppy
            @no_type_check
            def free_addr(self, addr: tuple[int, int]) -> None:
                # Callers have already consumed the corresponding physical block.
                self.addr_stack.push(addr)
                self.data_block_count -= 1

            @guppy
            @no_type_check
            def allocate_next_addr(self: "STATE") -> tuple[int, int]:
                if len(self.addr_stack) == 0:
                    exit("allocate_next_addr: No more logical qubits to allocate")
                next_addr = self.addr_stack.pop()

                if not self.blocks.is_borrowed(next_addr[0]):
                    # Since Steane is k=1, blocks are either not allocated, or
                    # completely filled, so this should never happen.
                    panic("allocate_next_addr: Next block was already allocated.")

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
                        blk = self.blocks.take(i)

                        qec_cycle_def(self, blk)

                        self.blocks.put(blk, i)
                        self.qec_counter[i] = 0.0

        match qec_policy.style:
            case QECStyle.Knill:

                @guppy
                @no_type_check
                def qec_gadget(
                    q: LogicalBlock[7], zero_states: array[LogicalBlock[7], 2] @ owned
                ) -> None:
                    a0, a1 = zero_states
                    knill_qec_cycle(q, a0, a1)

                @guppy
                @no_type_check
                def qec_cycle_def(state: STATE, q: LogicalBlock[7]) -> None:
                    state.with_zero_states(q, qec_gadget)

            case QECStyle.Steane:

                @guppy
                @no_type_check
                def qec_x_gadget(
                    q: LogicalBlock[7], zero_states: array[LogicalBlock[7], 1] @ owned
                ) -> None:
                    (a,) = zero_states
                    steane_x_qec_cycle(q, a)

                @guppy
                @no_type_check
                def qec_z_gadget(
                    q: LogicalBlock[7], zero_states: array[LogicalBlock[7], 1] @ owned
                ) -> None:
                    (a,) = zero_states
                    steane_z_qec_cycle(q, a)

                @guppy
                @no_type_check
                def qec_cycle_def(state: STATE, q: LogicalBlock[7]) -> None:
                    # Consume the first resource before acquiring the second.
                    state.with_zero_states(q, qec_x_gadget)
                    state.with_zero_states(q, qec_z_gadget)

            case QECStyle.Reichardt:

                @guppy
                @no_type_check
                def qec_cycle_def(state: STATE, q: LogicalBlock[7]) -> None:
                    reichardt_qec_cycle(q)

        @_register_op_replacement(steane_ops.qec_cycle_def)
        @no_type_check
        def _qec_cycle(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                blk = state.blocks.take(blk_id)

                qec_cycle_def(state, blk)

                state.blocks.put(blk, blk_id)
                state.qec_counter[blk_id] = 0.0

                return state, q

            return map_global(_impl, q)

        # TODO Defining the primitives to use the global state requires
        # a lot of "boilerplate" code. We should provide helper methods
        # to easily define these functions from the primitives. I think
        # this could be replaced with `@custom_function` and a custom
        # compiler.
        # See https://github.com/Quantinuum/guppyft/issues/161.
        @_register_op_replacement(steane_ops.prep_zero_def)
        @no_type_check
        def _prep_zero() -> tuple[tuple[int, int]]:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_next_addr()
                blk = state.get_zero_state()
                state.blocks.put(blk, blk_id)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.prep_zero))

                return state, (blk_id, qb_id)

            return map_global(_impl)

        @_register_op_replacement(steane_ops.prep_t_state_def)
        @no_type_check
        def _prep_t_state() -> tuple[tuple[int, int]]:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_next_addr()
                blk = state.get_magic_state()
                state.blocks.put(blk, blk_id)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.prep_t))

                return state, (blk_id, qb_id)

            return map_global(_impl)

        @_register_op_replacement(steane_ops.measure_z_def)
        @no_type_check
        def _measure_z(q: tuple[int, int]) -> RawMeasurement[7]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, RawMeasurement[7]]:
                blk_id, _ = q
                blk = state.blocks.take(blk_id)

                res = measure_z(blk)

                state.free_addr(q)
                return state, res

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.free_def)
        @no_type_check
        def _free(q: tuple[int, int]) -> None:
            @guppy
            def _impl(state: STATE @ owned, q: tuple[int, int]) -> STATE:
                blk_id, _ = q
                blk = state.blocks.take(blk_id)

                blk.discard()

                state.free_addr(q)
                return state

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.x_def)
        @no_type_check
        def _x(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                x(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.x))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.y_def)
        @no_type_check
        def _y(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                y(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.y))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.z_def)
        @no_type_check
        def _z(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                z(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.z))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.h_def)
        @no_type_check
        def _h(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                h(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.h))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.s_def)
        @no_type_check
        def _s(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                s(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.s))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.sdg_def)
        @no_type_check
        def _sdg(q: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                sdg(state.blocks[blk_id])

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.sdg))

                return state, q

            return map_global(_impl, q)

        @_register_op_replacement(steane_ops.inject_t_def)
        @no_type_check
        def _inject_t(q: tuple[int, int], a: tuple[int, int]) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int], a: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                resource = state.blocks.take(a[0])
                inject_t(state.blocks[blk_id], resource)
                state.free_addr(a)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.inject_t))

                return state, q

            return map_global(_impl, q, a)

        @_register_op_replacement(steane_ops.inject_tdg_def)
        @no_type_check
        def _inject_tdg(
            q: tuple[int, int], a: tuple[int, int]
        ) -> tuple[tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q: tuple[int, int], a: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int]]:
                blk_id, _ = q
                resource = state.blocks.take(a[0])
                inject_tdg(state.blocks[blk_id], resource)
                state.free_addr(a)

                state.qec_policy(array(blk_id), comptime(qec_policy.costs.inject_tdg))

                return state, q

            return map_global(_impl, q, a)

        @_register_op_replacement(steane_ops.cx_def)
        @no_type_check
        def _cx(
            ctl: tuple[int, int], tgt: tuple[int, int]
        ) -> tuple[tuple[int, int], tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, ctl: tuple[int, int], tgt: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int], tuple[int, int]]:
                cx(state.blocks[ctl[0]], state.blocks[tgt[0]])

                state.qec_policy(array(ctl[0], tgt[0]), comptime(qec_policy.costs.cx))

                return state, ctl, tgt

            return map_global(_impl, ctl, tgt)

        @_register_op_replacement(steane_ops.cz_def)
        @no_type_check
        def _cz(
            q0: tuple[int, int], q1: tuple[int, int]
        ) -> tuple[tuple[int, int], tuple[int, int]]:
            @guppy
            def _impl(
                state: STATE @ owned, q0: tuple[int, int], q1: tuple[int, int]
            ) -> tuple[STATE, tuple[int, int], tuple[int, int]]:
                cz(state.blocks[q0[0]], state.blocks[q1[0]])

                state.qec_policy(array(q0[0], q1[0]), comptime(qec_policy.costs.cz))

                return state, q0, q1

            return map_global(_impl, q0, q1)

        @_register_op_replacement(steane_ops.decode_def)
        @no_type_check
        def _decode(m: RawMeasurement[7] @ owned) -> bool:
            return decode(m)

        @guppy.declare
        @no_type_check
        @link_name("guppyft.steane.gen_state")
        def state_gen_decl() -> STATE: ...
        @lib.register_member
        @guppy
        @no_type_check
        @link_name("guppyft.steane.gen_state")
        def state_gen() -> STATE:
            return STATE(
                empty_array(),
                Stack(array(some((blk, 1)) for blk in range(n_blocks)), n_blocks),
                # qec_counter
                array(0.0 for _ in range(n_blocks)),
                # Data blocks count
                0,
                # Zero state factory
                StateFactory(
                    prep_zero_ft,
                    comptime(self._options.zero_factory_conf.max_attempts),
                    empty_queue(),
                ),
                # Magic state factory
                StateFactory(
                    prep_t_state_ft,
                    comptime(self._options.magic_factory_conf.max_attempts),
                    empty_queue(),
                ),
            )

        @guppy.declare
        @no_type_check
        @link_name("guppyft.steane.discard_state")
        def state_discard_decl(state: "STATE" @ owned) -> None: ...
        @lib.register_member
        @guppy
        @no_type_check
        @link_name("guppyft.steane.discard_state")
        def state_discard(state: "STATE" @ owned) -> None:
            state.blocks.discard_all_taken()
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

        ops.register_for_elimination_check(steane_ops().name)
        tys = TyReplacements().with_types(
            [
                ("guppyft.steane.types", "qubit"),
                ("guppyft.steane.types", "measurement"),
            ]
        )

        return ImplementOpsSpec(
            ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib.compile()]
        )

    def _gen_encoder_spec(self, n_blocks: int) -> EncodeSpec:
        """Generate the full `EncoderSpec` (logical encoding + op implementations)
        for a program using `n_blocks` logical blocks."""
        impl_spec = self._gen_implement_spec(n_blocks)

        ext = ExtensionRegistry.from_extensions(
            [steane_ops(), steane_types(), std_ops(), std_types(), rotation()]
        )
        # `_std_extensions` should not be necessary but seems to be
        #  required for `borrow_array` when (de)serializing.
        ext.extend(_std_extensions())

        logical_compiler = ReplacementCompiler(
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
                ("tket.quantum", "CZ"): ("guppyft.steane.ops", "cz", []),
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

        return EncodeSpec(
            compile=logical_compiler, implement_ops=ImplementOps.for_spec(impl_spec)
        )

    def with_qec_policy(self, qec_policy: QECPolicy) -> Self:
        """Set the QEC policy."""
        return replace(self, _options=replace(self._options, qec_policy=qec_policy))

    def with_zero_factory_conf(self, conf: RUSStateFactoryConf) -> Self:
        """Set the zero state factory configuration."""
        return replace(self, _options=replace(self._options, zero_factory_conf=conf))

    def with_magic_factory_conf(self, conf: RUSStateFactoryConf) -> Self:
        """Set the magic state factory configuration."""
        return replace(self, _options=replace(self._options, magic_factory_conf=conf))

    def build(self, n_blocks: int) -> SteaneInstance:
        """Build a `SteaneInstance` limited to `n_blocks` across program blocks,
        factory candidates and QEC resource blocks."""
        encoder_spec = self._gen_encoder_spec(n_blocks)
        return SteaneInstance(
            _spec=encoder_spec, _n_blocks=n_blocks, _options=deepcopy(self._options)
        )

    @classmethod
    def instance_from_params(cls, params: dict[str, Any]) -> "SteaneInstance":
        """Produces an instance with the builder according to the given parameters. To
        be used as the 'inverse' of `SteaneInstance.annotate`."""
        params = PathDict(params)

        builder = cls()
        if params["schema_version"] != _SCHEMA_VERSION:
            raise RuntimeError(
                f"Unsupported params schema version: {params['schema_version']}"
            )

        if (zero_factory_params := params.get("zero_factory")) is not None:
            builder = builder.with_zero_factory_conf(
                RUSStateFactoryConf.from_json(
                    zero_factory_params,
                    defaults_from=builder._options.zero_factory_conf,
                )
            )
        if (magic_factory_params := params.get("magic_factory")) is not None:
            builder = builder.with_magic_factory_conf(
                RUSStateFactoryConf.from_json(
                    magic_factory_params,
                    defaults_from=builder._options.magic_factory_conf,
                )
            )
        if (qec_policy_params := params.get("qec_policy")) is not None:
            builder = builder.with_qec_policy(QECPolicy.from_json(qec_policy_params))

        return builder.build(n_blocks=params["n_blocks"])
