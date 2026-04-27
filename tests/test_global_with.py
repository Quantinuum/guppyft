from guppylang import guppy
from guppylang.std.builtins import result
from guppylang.std.quantum import discard, qubit, measure, x
from hugr.qsystem.result import QsysShot

from .utils.global_swap import map_global_state_generic, with_global_state_generic


def test_with():
    @guppy
    def foo(qb: qubit, i: tuple[int, int]) -> int:
        x(qb)
        return i[0] + i[1]

    @guppy
    def my_prog() -> None:
        discard(qubit())
        i = map_global_state_generic(foo, (9, 10))
        result("my_prog", i)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state_generic(qb, my_prog)
        result("qb_main", measure(qb))

    res = QsysShot(main.emulator(n_qubits=2).run())

    assert res.entries[0][0] == ("my_prog", 19)
    assert res.entries[0][1] == ("qb_main", 1)
