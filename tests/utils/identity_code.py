from guppylang import guppy
from guppylang.std.builtins import array, comptime, exit, owned
from guppylang.std.collections import Stack
from guppylang.std.option import Option, nothing, some
from guppylang.std.quantum import cx, discard, measure, project_z, qubit, x

from guppyft.spec import EncoderSpec

from .global_swap import swap_global_state_generic


def identity_code_gen(
    n_qubits: int,
) -> EncoderSpec:
    @guppy
    def swap_global_state(
        new_value: Option["GLOBAL_STATE"] @ owned,
    ) -> Option["GLOBAL_STATE"]:
        return swap_global_state_generic(new_value)

    @guppy.struct
    class GLOBAL_STATE:
        blocks: array[Option[qubit], comptime(n_qubits)]
        addr_stack: Option[Stack[tuple[int, int], comptime(n_qubits)]]

        @guppy
        def get_next_addr(
            self: "GLOBAL_STATE",
        ) -> tuple[int, int]:
            stack = self.addr_stack.take().unwrap()
            if stack.end == 0:
                exit("get_next_addr: No more qubits to allocate")
            next_addr, stack = stack.pop()
            self.addr_stack.swap(some(stack)).unwrap_nothing()

            return next_addr

        @guppy
        def discard(self: "GLOBAL_STATE" @ owned) -> None:
            for qb in self.blocks:
                if qb.is_some():
                    qb.unwrap().discard()
                else:
                    qb.unwrap_nothing()

    @guppy(link_name="tket.quantum.QAlloc")
    def _QAlloc() -> tuple[tuple[int, int]]:
        global_state = swap_global_state(nothing()).unwrap()

        blk_id, qb_id = global_state.get_next_addr()

        blk = qubit()

        global_state.blocks[blk_id].swap(some(blk)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

        return ((blk_id, qb_id),)

    # MeasureFree is compiled from `guppylang.std.quantum.measure`
    @guppy(link_name="tket.quantum.MeasureFree")
    def _MeasureFree(q: tuple[int, int]) -> bool:
        blk_id, qb_id = q
        global_state = swap_global_state(nothing()).unwrap()

        blk: qubit = global_state.blocks[blk_id].take().unwrap()

        res = measure(blk)

        addr_stack = global_state.addr_stack.take().unwrap()
        addr_stack = addr_stack.push((blk_id, qb_id))
        global_state.addr_stack.swap(some(addr_stack)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

        return res

    # Measure is compiled from `guppylang.std.quantum.project_z`
    @guppy(link_name="tket.quantum.Measure")
    def _Measure(q: tuple[int, int]) -> tuple[tuple[int, int], bool]:
        blk_id, qb_id = q
        global_state = swap_global_state(nothing()).unwrap()

        # Get qubit from global state, project_z and return
        blk: qubit = global_state.blocks[blk_id].take().unwrap()
        res = project_z(blk)
        global_state.blocks[blk_id].swap(some(blk)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

        return (blk_id, qb_id), res

    # QFree is compiled from `guppylang.std.quantum.discard`
    @guppy(link_name="tket.quantum.QFree")
    def _QFree(q: tuple[int, int]) -> None:
        blk_id, qb_id = q
        global_state = swap_global_state(nothing()).unwrap()

        # Get qubit and discard
        blk: qubit = global_state.blocks[blk_id].take().unwrap()
        discard(blk)

        # Push addr back to the stack
        addr_stack = global_state.addr_stack.take().unwrap()
        addr_stack = addr_stack.push((blk_id, qb_id))
        global_state.addr_stack.swap(some(addr_stack)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

    @guppy(link_name="tket.quantum.X")
    def _X(q: tuple[int, int]) -> tuple[tuple[int, int]]:
        blk_id, qb_id = q
        global_state = swap_global_state(nothing()).unwrap()

        blk = global_state.blocks[blk_id].take().unwrap()

        x(blk)

        global_state.blocks[blk_id].swap(some(blk)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

        return ((blk_id, qb_id),)

    @guppy(link_name="tket.quantum.CX")
    def _CX(
        ctl: tuple[int, int], tgt: tuple[int, int]
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        global_state = swap_global_state(nothing()).unwrap()

        ctl_blk = global_state.blocks[ctl[0]].take().unwrap()
        tgt_blk = global_state.blocks[tgt[0]].take().unwrap()

        cx(ctl_blk, tgt_blk)

        global_state.blocks[ctl[0]].swap(some(ctl_blk)).unwrap_nothing()
        global_state.blocks[tgt[0]].swap(some(tgt_blk)).unwrap_nothing()

        swap_global_state(some(global_state)).unwrap_nothing()

        return ctl, tgt

    logical_ops = {
        ("tket.quantum", "QAlloc"): _QAlloc,
        ("tket.quantum", "MeasureFree"): _MeasureFree,
        ("tket.quantum", "Measure"): _Measure,
        ("tket.quantum", "QFree"): _QFree,
        ("tket.quantum", "X"): _X,
        ("tket.quantum", "CX"): _CX,
    }

    @guppy
    def global_state_gen() -> GLOBAL_STATE:
        return GLOBAL_STATE(
            array(nothing[qubit]() for _ in range(comptime(n_qubits))),
            some(
                Stack(
                    array(some((blk, 1)) for blk in range(comptime(n_qubits))),
                    comptime(n_qubits),
                )
            ),
        )

    @guppy
    def setup() -> None:
        global_state = global_state_gen()
        swap_global_state(some(global_state)).unwrap_nothing()

    @guppy
    def teardown() -> None:
        swap_global_state(nothing()).unwrap().discard()

    return EncoderSpec(
        ops=logical_ops,
        setup=setup,
        teardown=teardown,
        tket_passes=[],
    )
