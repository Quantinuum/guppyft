from collections import defaultdict
from typing import no_type_check

import tket.extensions
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.angles import angle
from guppylang.std.builtins import array, comptime, owned, result
from guppylang.std.collections import Stack
from guppylang.std.option import Option, nothing, some
from guppylang.std.qsystem.helios import zz_phase
from guppylang.std.quantum import cx, discard, measure, project_z, qubit, x

from guppyft.encode import EncoderSpec, ImplementOpsSpec, OpReplacements
from guppyft.encode._implement_ops import TyReplacements
from guppyft.globals import map_global, with_global

N = guppy.nat_var("N")


def identity_code_spec(
    n_qubits: int,
    qec_budget: int = 1,
    costs: dict[str, int] | None = None,
) -> EncoderSpec:
    if costs is None:
        costs = defaultdict(int)

    @guppy.struct
    class STATE:
        blocks: array[Option[qubit], comptime(n_qubits)]  # type: ignore[type-arg,valid-type]
        addr_stack: Stack[tuple[int, int], comptime(n_qubits)]  # type: ignore[type-arg,valid-type]

        qec_counter: array[int, comptime(n_qubits)]  # type: ignore[valid-type]

        @guppy
        @no_type_check
        def free_addr(self, addr: tuple[int, int]) -> None:
            self.addr_stack.push(addr)

        @guppy
        @no_type_check
        def get_next_addr(
            self: "STATE",
        ) -> tuple[int, int]:
            if len(self.addr_stack) == 0:
                exit("get_next_addr: No more qubits to allocate")
            next_addr = self.addr_stack.pop()

            return next_addr

        @guppy
        @no_type_check
        def discard(self: "STATE" @ owned) -> None:
            for qb in self.blocks:
                if qb.is_some():
                    qb.unwrap().discard()
                else:
                    qb.unwrap_nothing()

        @guppy
        @no_type_check
        def take_block(self, blk_id: int) -> qubit:
            return self.blocks[blk_id].take().unwrap()

        @guppy
        @no_type_check
        def put_block(self, blk_id: int, blk: qubit @ owned) -> None:
            self.blocks[blk_id].swap(some(blk)).unwrap_nothing()

        @guppy
        @no_type_check
        def qec_policy(
            self: "STATE",
            blk_ids: array[int, N],
            cost_op: int,
            cost_idle: int,
        ) -> None:
            # Array of idle costs
            cost_to_apply = array(cost_idle for _ in range(comptime(n_qubits)))

            # Replace with op noise for necessary blocks
            for i in blk_ids.copy():
                cost_to_apply[i] = cost_op

            # Add costs to counter and reset counter
            for i in range(comptime(n_qubits)):
                self.qec_counter[i] += cost_to_apply[i]

                if self.qec_counter[i] >= comptime(qec_budget):
                    result("qec_counter", self.qec_counter)
                    self.qec_counter[i] = 0

    @guppy
    @link_name("link.identity.QAlloc")
    @no_type_check
    def _QAlloc() -> tuple[tuple[int, int]]:
        @guppy
        def _impl(state: STATE @ owned) -> tuple[STATE, tuple[int, int]]:
            result("_QAlloc", 0)
            blk_id, qb_id = state.get_next_addr()
            state.put_block(blk_id, qubit())
            return state, (blk_id, qb_id)

        return map_global(_impl)

    # MeasureFree is compiled from `guppylang.std.quantum.measure`
    @guppy
    @link_name("link.identity.MeasureFree")
    @no_type_check
    def _MeasureFree(q: tuple[int, int]) -> bool:
        @guppy
        def _impl(state: STATE @ owned, q: tuple[int, int]) -> tuple[STATE, bool]:
            result("_MeasureFree", 0)
            blk_id, _ = q
            blk = state.take_block(blk_id)

            res = measure(blk).read()

            state.free_addr(q)
            return state, res

        return map_global(_impl, q)

    # Measure is compiled from `guppylang.std.quantum.project_z`
    @guppy
    @link_name("link.identity.Measure")
    @no_type_check
    def _Measure(q: tuple[int, int]) -> tuple[tuple[int, int], bool]:
        @guppy
        def _impl(
            state: STATE @ owned, q: tuple[int, int]
        ) -> tuple[STATE, tuple[int, int], bool]:
            result("_Measure", 0)
            blk_id, qb_id = q
            blk = state.take_block(blk_id)

            res = project_z(blk).read()

            state.put_block(blk_id, blk)
            return state, (blk_id, qb_id), res

        return map_global(_impl, q)

    # Replacement for `tket.measurement.Read` operation
    @guppy
    @link_name("link.identity.Read")
    @no_type_check
    def _Read(m: bool) -> bool:
        return m

    # QFree is compiled from `guppylang.std.quantum.discard`
    @guppy
    @link_name("link.identity.QFree")
    @no_type_check
    def _QFree(q: tuple[int, int]) -> None:
        @guppy
        def _impl(state: STATE @ owned, q: tuple[int, int]) -> STATE:
            result("_QFree", 0)
            blk_id, _ = q
            blk = state.take_block(blk_id)
            discard(blk)
            state.free_addr(q)
            return state

        return map_global(_impl, q)

    @guppy
    @link_name("link.identity.X")
    @no_type_check
    def _X(q: tuple[int, int]) -> tuple[tuple[int, int]]:
        @guppy
        def _impl(
            state: STATE @ owned, q: tuple[int, int]
        ) -> tuple[STATE, tuple[int, int]]:
            result("_X", 0)
            blk_id, qb_id = q
            blk = state.take_block(blk_id)

            x(blk)

            state.put_block(blk_id, blk)

            state.qec_policy(
                array(blk_id), comptime(costs["X"]), comptime(costs["IDLE_X"])
            )

            return state, (blk_id, qb_id)

        return map_global(_impl, q)

    @guppy
    @link_name("link.identity.CX")
    @no_type_check
    def _CX(
        ctl: tuple[int, int], tgt: tuple[int, int]
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        @guppy
        def _impl(
            state: STATE @ owned, ctl: tuple[int, int], tgt: tuple[int, int]
        ) -> tuple[STATE, tuple[int, int], tuple[int, int]]:
            result("_CX", 0)
            ctl_blk, tgt_blk = state.take_block(ctl[0]), state.take_block(tgt[0])

            cx(ctl_blk, tgt_blk)

            state.put_block(ctl[0], ctl_blk), state.put_block(tgt[0], tgt_blk)

            state.qec_policy(
                array(ctl[0], tgt[0]), comptime(costs["CX"]), comptime(costs["IDLE_CX"])
            )
            return state, ctl, tgt

        return map_global(_impl, ctl, tgt)

    @guppy
    @link_name("link.identity.ZZPhase")
    @no_type_check
    def _ZZPhase(
        ctl: tuple[int, int], tgt: tuple[int, int], phase: float
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        @guppy
        def _impl(
            state: STATE @ owned, args: tuple[tuple[int, int], tuple[int, int], float]
        ) -> tuple[STATE, tuple[int, int], tuple[int, int]]:
            result("_ZZPhase", 0)
            ctl, tgt, theta = args
            ctl_blk, tgt_blk = state.take_block(ctl[0]), state.take_block(tgt[0])

            zz_phase(ctl_blk, tgt_blk, angle(theta))

            state.put_block(ctl[0], ctl_blk), state.put_block(tgt[0], tgt_blk)

            state.qec_policy(
                array(ctl[0], tgt[0]),
                comptime(costs["ZZPhase"]),
                comptime(costs["IDLE_ZZPhase"]),
            )
            return state, ctl, tgt

        return map_global(_impl, (ctl, tgt, phase))

    @guppy.declare
    @link_name("link.identity.gen_state")
    @no_type_check
    def state_gen_decl() -> STATE: ...

    @guppy
    @link_name("link.identity.gen_state")
    @no_type_check
    def state_gen() -> STATE:
        return STATE(
            array(nothing[qubit]() for _ in range(comptime(n_qubits))),
            Stack(
                array(some((blk, 1)) for blk in range(comptime(n_qubits))),
                comptime(n_qubits),
            ),
            array(0 for _ in range(comptime(n_qubits))),
        )

    @guppy.declare
    @link_name("link.identity.discard_state")
    @no_type_check
    def state_discard_decl(state: STATE @ owned) -> None: ...

    @guppy
    @link_name("link.identity.discard_state")
    @no_type_check
    def state_discard(state: STATE @ owned) -> None:
        state.discard()

    lib = GuppyLibrary.from_members(
        state_gen,
        state_discard,
        _QAlloc,
        _MeasureFree,
        _Measure,
        _Read,
        _QFree,
        _X,
        _CX,
        _ZZPhase,
    ).compile()

    ops = OpReplacements()
    ops.with_generated_decls(
        {
            ("tket.quantum", "QAlloc"): "link.identity.QAlloc",
            ("tket.quantum", "MeasureFree"): "link.identity.MeasureFree",
            ("tket.quantum", "Measure"): "link.identity.Measure",
            ("tket.measurement", "Read"): "link.identity.Read",
            ("tket.quantum", "QFree"): "link.identity.QFree",
            ("tket.quantum", "X"): "link.identity.X",
            ("tket.quantum", "CX"): "link.identity.CX",
            # `tket.qsystem` extension may not be loaded in programs that only use
            # `guppyland.std.quantum` operations. `ZZPhase` is included to test
            # missing extension behaviour during encoding.
            ("tket.qsystem.helios", "ZZPhase"): "link.identity.ZZPhase",
        }
    )

    tys = TyReplacements()
    tys.with_types([tket.extensions.measurement.measurement_t, ("prelude", "qubit")])

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

    return EncoderSpec(
        implement_spec=ImplementOpsSpec(
            ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib]
        )
    )
