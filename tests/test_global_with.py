import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorError
from guppylang.std.builtins import result
from guppylang.std.quantum import measure, qubit, x

from guppyft.globals import map_global_state, with_global_state


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


def test_map_no_input() -> None:
    @guppy
    def foo(qb: qubit) -> int:
        x(qb)
        return 19

    @guppy
    def my_prog() -> None:
        i = map_global_state(foo)
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


# This will fail as order edges are not added to the map function call with return
# type None. Tracking issue:
# https://github.com/Quantinuum/guppylang/issues/1624
@pytest.mark.xfail
def test_map_return_none() -> None:
    @guppy
    def foo(qb: qubit) -> None:
        x(qb)
        result("foo", 19)

    @guppy
    def my_prog() -> None:
        map_global_state(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        result("qb_main", measure(qb))

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "qb_main": [1],
            "foo": [19],
        }
    ]


def test_map_return_tuple() -> None:
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


def test_map_without_with() -> None:
    @guppy
    def foo(qb: qubit, i: tuple[int, int]) -> int:
        x(qb)
        return i[0] + i[1]

    @guppy
    def main() -> None:
        i = map_global_state(foo, (9, 10))
        result("my_prog", i)

    with pytest.raises(EmulatorError) as _:
        main.emulator(n_qubits=1).run().collated_shots()
