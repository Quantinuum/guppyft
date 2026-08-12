from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.collections import Stack
from guppylang.std.option import Option, nothing, some
from guppylang.std.platform import panic, result
from hugr.ext import ExtensionRegistry
from hugr.package import Package
from hugr.std import _std_extensions

from guppyft.code.steane.primitives import (
    cx,
    decode,
    h,
    measure_z,
    prep_zero_non_ft,
    x,
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


@dataclass(frozen=True, kw_only=True)
class SteaneEncoderParams(EncoderParams):
    n_blocks: int

    def encoding(self) -> str:
        return "steane"

    def params(self) -> Mapping[str, Any]:
        return {"n_blocks": self.n_blocks}


class QECStyle(Enum):
    Shor = 0
    Knill = 1
    Steane = 2


@dataclass
class QECPolicy:
    style: QECStyle
    threshold: int
    costs: dict[str, int]


@dataclass
class SteaneSpec:
    n_blocks: int
    qec_policy: QECPolicy = field(
        default_factory=lambda: QECPolicy(QECStyle.Shor, 1, defaultdict())
    )

    def gen_implement_spec(self) -> ImplementOpsSpec:
        # TODO STATE should be generic for all codes. The methods that are code specific
        # should be `@guppy.declare` and each code can provide an implementation to be
        # linked i.e. `allocate_next_addr`.
        # See https://github.com/quantinuum-dev/guppyft/issues/179
        @guppy.struct
        class STATE:
            blocks: array[Option[LogicalBlock[7]], comptime(self.n_blocks)]  # type: ignore[valid-type,type-arg]
            addr_stack: Stack[tuple[int, int], comptime(self.n_blocks)]  # type: ignore[valid-type,type-arg]
            qec_counter: array[int, comptime(self.n_blocks)]  # type: ignore[valid-type]

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

                return next_addr

            @guppy
            @no_type_check
            def qec_policy(
                self,
                blk_ids: array[int, N] @ owned,
                op_cost: int,
            ) -> None:
                for i in blk_ids:
                    self.qec_counter[i] = self.qec_counter[i] + op_cost

                    if self.qec_counter[i] >= comptime(self.qec_policy.threshold):
                        blk = self.take_block(i)

                        qec_cycle(self, blk)

                        self.put_block(i, blk)
                        self.qec_counter[i] = 0

        @guppy
        @no_type_check
        def qec_cycle(state: STATE, blk: LogicalBlock[7]) -> STATE:
            result("qec_counter", state.qec_counter)
            return state

        # TODO Defining the primitives to use the global state requires
        # a lot of "boilerplate" code. We should provide helper methods
        # to easily define these functions from the primitives. I think
        # this could be replaced with `@custom_function` and a custom
        # compiler.
        # See https://github.com/quantinuum-dev/guppyft/issues/161.
        @guppy
        @no_type_check
        @link_name("guppyft.steane._prep_zero_non_ft")
        def _prep_zero_non_ft() -> tuple[tuple[int, int]]:
            @guppy
            def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
                blk_id, qb_id = state.allocate_next_addr()
                blk = prep_zero_non_ft()
                state.put_block(blk_id, blk)
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
                return state, q

            return map_global(_impl, q)

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
                array(
                    nothing[LogicalBlock[7]]() for _ in range(comptime(self.n_blocks))
                ),
                Stack(
                    array(some((blk, 1)) for blk in range(comptime(self.n_blocks))),
                    comptime(self.n_blocks),
                ),
                # qec_counter
                array(0 for _ in range(comptime(self.n_blocks))),
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
            _prep_zero_non_ft,
            _measure_z,
            _free,
            decode,
            _x,
            _z,
            _h,
            _cx,
        ).compile()

        ops = OpReplacements().with_generated_decls(
            {
                ("guppyft.steane.ops", "prep_zero"): "guppyft.steane._prep_zero_non_ft",
                ("guppyft.steane.ops", "measure_z"): "guppyft.steane._measure_z",
                ("guppyft.steane.ops", "free"): "guppyft.steane._free",
                ("guppyft.steane.ops", "x"): "guppyft.steane._x",
                ("guppyft.steane.ops", "z"): "guppyft.steane._z",
                ("guppyft.steane.ops", "h"): "guppyft.steane._h",
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

    def gen_encoder_spec(self) -> EncoderSpec:

        impl_spec = self.gen_implement_spec()

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
            },
            extensions=ext,
        )

        return EncoderSpec(to_logical=std_encoder, implement_spec=impl_spec)

    def encode(self, pkg: Package) -> Package:
        enc_spec = self.gen_encoder_spec()
        return encode(pkg, enc_spec)

    def implement_ops(self, pkg: Package) -> Package:
        implement_spec = self.gen_implement_spec()
        return implement_ops(pkg, implement_spec)
