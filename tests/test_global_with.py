from guppylang import guppy
from guppylang.std.builtins import result
from guppylang.std.quantum import measure, qubit, x

from .utils.global_swap import map_global_state, with_global_state


def test_with() -> None:
    @guppy
    def foo(qb: qubit, i: tuple[int, int]) -> int:
        x(qb)
        return i[0] + i[1]

    @guppy
    def my_prog() -> None:
        i = map_global_state(foo, (9, 10))
        result("my_prog", i)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        result("qb_main", measure(qb))

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "qb_main": [1],
            "my_prog": [19],
        }
    ]


def test_map_tuple_return() -> None:
    @guppy
    def foo(qb: qubit, i: tuple[int, int]) -> tuple[int, int]:
        x(qb)
        return i

    @guppy
    def my_prog() -> None:
        i = map_global_state(foo, (9, 10))
        result("my_prog", i[0] + i[1])

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        result("qb_main", measure(qb))

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "qb_main": [1],
            "my_prog": [19],
        }
    ]
