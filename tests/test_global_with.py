import re
from typing import no_type_check

import pytest
from guppylang import array, guppy
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


def test_nested_with() -> None:
    @guppy
    @no_type_check
    def foo(i: array[int, 1], j: int) -> int:
        i[0] = i[0] + j
        return i[0] + j

    @guppy
    def my_nested_prog() -> None:
        i = map_global_state(foo, 1)
        result("my_nested_prog", i)

    @guppy
    def my_prog() -> None:
        arr_inner = array(10)
        arr_inner = with_global_state(arr_inner, my_nested_prog)
        result("arr_inner", arr_inner)
        i = map_global_state(foo, 1)
        result("my_prog", i)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global_state(arr_outer, my_prog)
        result("arr_outer", arr_outer)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "my_nested_prog": [12],
            "arr_inner": [[11]],
            "my_prog": [2],
            "arr_outer": [[1]],
        }
    ]


def test_mismatch_type() -> None:
    @guppy
    @no_type_check
    def foo(arr: array[int, 1]) -> int:
        return arr[0]

    @guppy
    def my_prog() -> None:
        i = map_global_state(foo)
        result("my_prog", i)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        result("main", measure(qb))

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Failed to emit LLVM for function tests.test_global_with."
            "test_mismatch_type.<locals>.my_prog at node Node(17)"
        ),
    ) as _:
        main.emulator(n_qubits=1).run().collated_shots()


@pytest.mark.xfail
def test_non_linear_global() -> None:
    @guppy
    def foo(i: int) -> int:
        i = i + 1
        return i

    @guppy
    def my_prog() -> None:
        i = map_global_state(foo)
        result("my_prog", i)

    @guppy
    def main() -> None:
        i = with_global_state(0, my_prog)
        result("main", i)

    main.emulator(n_qubits=1).run().collated_shots()
