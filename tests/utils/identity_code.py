from collections import defaultdict
from typing import no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, comptime, owned, result
from guppylang.std.collections import Stack
from guppylang.std.option import Option, nothing, some
from guppylang.std.quantum import cx, discard, measure, project_z, qubit, x

from guppyft.globals import map_global_state, with_global_state
from guppyft.spec import EncoderSpec, OpReplacements

N = guppy.nat_var("N")


def identity_code_gen(
    n_qubits: int,
    qec_budget: int = 1,
    costs: dict[str, int] = defaultdict(int),
) -> EncoderSpec:
    @guppy.struct
    class GLOBAL_STATE:
        blocks: array[Option[qubit], comptime(n_qubits)]  # type: ignore[type-arg,valid-type]
        addr_stack: Stack[tuple[int, int], comptime(n_qubits)]  # type: ignore[type-arg,valid-type]

        qec_counter: array[int, comptime(n_qubits)]  # type: ignore[valid-type]

        @guppy
        @no_type_check
        def free_addr(self, addr: tuple[int, int]) -> None:
            self.addr_stack = self.addr_stack.push(addr)

        @guppy
        @no_type_check
        def get_next_addr(
            self: "GLOBAL_STATE",
        ) -> tuple[int, int]:
            if self.addr_stack.end == 0:
                exit("get_next_addr: No more qubits to allocate")
            next_addr, self.addr_stack = self.addr_stack.pop()

            return next_addr

        @guppy
        @no_type_check
        def discard(self: "GLOBAL_STATE" @ owned) -> None:
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
            self: "GLOBAL_STATE",
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

    @guppy(link_name="link.QAlloc")
    @no_type_check
    def _QAlloc() -> tuple[tuple[int, int]]:
        @guppy
        def _impl(state: GLOBAL_STATE) -> tuple[tuple[int, int]]:
            result("_QAlloc", 0)
            blk_id, qb_id = state.get_next_addr()
            state.put_block(blk_id, qubit())
            return ((blk_id, qb_id),)

        return map_global_state(_impl)

    # MeasureFree is compiled from `guppylang.std.quantum.measure`
    @guppy(link_name="link.MeasureFree")
    @no_type_check
    def _MeasureFree(q: tuple[int, int]) -> bool:
        @guppy
        def _impl(state: GLOBAL_STATE, q: tuple[int, int]) -> bool:
            result("_MeasureFree", 0)
            blk_id, _ = q
            blk = state.take_block(blk_id)

            res = measure(blk)

            state.free_addr(q)
            return res

        return map_global_state(_impl, q)

    # Measure is compiled from `guppylang.std.quantum.project_z`
    @guppy(link_name="link.Measure")
    @no_type_check
    def _Measure(q: tuple[int, int]) -> tuple[tuple[int, int], bool]:
        @guppy
        def _impl(
            state: GLOBAL_STATE, q: tuple[int, int]
        ) -> tuple[tuple[int, int], bool]:
            result("_Measure", 0)
            blk_id, qb_id = q
            blk = state.take_block(blk_id)

            res = project_z(blk)

            state.put_block(blk_id, blk)
            return (blk_id, qb_id), res

        return map_global_state(_impl, q)

    # QFree is compiled from `guppylang.std.quantum.discard`
    @guppy(link_name="link.QFree")
    @no_type_check
    def _QFree(q: tuple[int, int]) -> None:
        # `_impl` requires a return type otherwise it will not be called.
        @guppy
        def _impl(state: GLOBAL_STATE, q: tuple[int, int]) -> None:
            result("_QFree", 0)
            blk_id, _ = q
            blk = state.take_block(blk_id)

            discard(blk)

            state.free_addr(q)

        # The return must be used otherwise the function is not called.
        return map_global_state(_impl, q)

    @guppy(link_name="link.X")
    @no_type_check
    def _X(q: tuple[int, int]) -> tuple[tuple[int, int]]:
        @guppy
        def _impl(state: GLOBAL_STATE, q: tuple[int, int]) -> tuple[tuple[int, int]]:
            result("_X", 0)
            blk_id, qb_id = q
            blk = state.take_block(blk_id)

            x(blk)

            state.put_block(blk_id, blk)

            state.qec_policy(
                array(blk_id), comptime(costs["X"]), comptime(costs["IDLE_X"])
            )

            return ((blk_id, qb_id),)

        return map_global_state(_impl, q)

    @guppy(link_name="link.CX")
    @no_type_check
    def _CX(
        ctl: tuple[int, int], tgt: tuple[int, int]
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        @guppy
        def _impl(
            state: GLOBAL_STATE, input: tuple[tuple[int, int], tuple[int, int]]
        ) -> tuple[tuple[int, int], tuple[int, int]]:
            result("_CX", 0)
            ctl, tgt = input
            ctl_blk, tgt_blk = state.take_block(ctl[0]), state.take_block(tgt[0])

            cx(ctl_blk, tgt_blk)

            state.put_block(ctl[0], ctl_blk), state.put_block(tgt[0], tgt_blk)

            state.qec_policy(
                array(ctl[0], tgt[0]), comptime(costs["CX"]), comptime(costs["IDLE_CX"])
            )
            return ctl, tgt

        return map_global_state(_impl, (ctl, tgt))

    ops = OpReplacements()
    ops.with_funcs(
        {
            ("tket.quantum", "QAlloc"): _QAlloc,
            ("tket.quantum", "MeasureFree"): _MeasureFree,
            ("tket.quantum", "Measure"): _Measure,
            ("tket.quantum", "QFree"): _QFree,
            ("tket.quantum", "X"): _X,
            ("tket.quantum", "CX"): _CX,
        }
    )

    @guppy
    @no_type_check
    def global_state_gen() -> GLOBAL_STATE:
        return GLOBAL_STATE(
            array(nothing[qubit]() for _ in range(comptime(n_qubits))),
            Stack(
                array(some((blk, 1)) for blk in range(comptime(n_qubits))),
                comptime(n_qubits),
            ),
            array(0 for _ in range(comptime(n_qubits))),
        )

    def build_wrapper(
        func: GuppyFunctionDefinition[[], None],
    ) -> GuppyFunctionDefinition[[], None]:
        @guppy
        @no_type_check
        def wrapper() -> None:
            state = global_state_gen()
            state = with_global_state(state, func)
            state.discard()

        return wrapper  # type: ignore[no-any-return]

    return EncoderSpec(ops=ops, build_wrapper=build_wrapper)
