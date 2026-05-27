import re
from typing import no_type_check

import pytest
from guppylang import array, guppy
from guppylang.emulator import EmulatorError
from guppylang.std.builtins import result
from guppylang.std.quantum import discard, measure, qubit, x

from guppyft.globals import map_global, with_global


def test_with_map() -> None:
    @guppy
    def foo(i: tuple[int, int], qb: qubit) -> int:
        x(qb)
        return i[0] + i[1]

    @guppy
    def my_prog() -> None:
        i = map_global(foo, (9, 10))
        result("my_prog", i)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
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
        i = map_global(foo)
        result("my_prog", i)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
        result("qb_main", measure(qb))

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "qb_main": [1],
            "my_prog": [19],
        }
    ]


def test_map_return_none() -> None:
    @guppy
    def foo(qb: qubit) -> None:
        x(qb)
        result("foo", 19)

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
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
    def foo(
        i: tuple[int, int],
        qb: qubit,
    ) -> tuple[int, int]:
        x(qb)
        return i

    @guppy
    def my_prog() -> None:
        i = map_global(foo, (9, 10))
        result("my_prog", i[0] + i[1])

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
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
    def foo(qb: qubit) -> None:
        x(qb)

    @guppy
    def main() -> None:
        map_global(foo)

    with pytest.raises(EmulatorError) as _:
        main.emulator(n_qubits=1).run().collated_shots()


def test_nested_with() -> None:
    @guppy
    @no_type_check
    def foo(j: int, i: array[int, 1]) -> None:
        i[0] = i[0] + j

    @guppy
    def my_nested_prog() -> None:
        map_global(foo, 1)

    @guppy
    def my_prog() -> None:
        map_global(foo, 1)
        arr_inner = array(10)
        arr_inner = with_global(my_nested_prog, arr_inner)
        result("arr_inner", arr_inner)
        map_global(foo, 2)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global(my_prog, arr_outer)
        result("arr_outer", arr_outer)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "arr_inner": [[11]],
            "arr_outer": [[3]],
        }
    ]


def test_mismatch_type() -> None:
    @guppy
    @no_type_check
    def foo(arr: array[int, 1]) -> int:
        return arr[0]

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
        discard(qb)

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Failed to emit LLVM for function tests.test_global.test_mismatch_type"
            ".<locals>.my_prog at node Node(15)"
        ),
    ) as _:
        main.emulator(n_qubits=1).run().collated_shots()


def test_non_linear_global() -> None:
    @guppy
    def foo(i: int) -> int:
        result("foo", i)
        return i

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        with_global(my_prog, 0)

    with pytest.raises(
        TypeError, match=r"Global arg must be linear. Found int<6>."
    ) as _:
        main.emulator(n_qubits=1).run().collated_shots()


def test_linear_input_no_output() -> None:
    @guppy
    @no_type_check
    def foo(arr: array[int, 2], qb: qubit) -> None:
        result("foo", arr)
        x(qb)

    @guppy
    def my_prog() -> None:
        map_global(foo, array(0, 1))

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
        discard(qb)

    res = main.emulator(n_qubits=1).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
        }
    ]


def test_linear_input_with_output() -> None:
    @guppy
    @no_type_check
    def foo(arr: array[int, 2], qb: qubit) -> int:
        result("foo", arr)
        x(qb)
        return 0

    @guppy
    def my_prog() -> None:
        ret = map_global(foo, array(0, 1))
        result("my_prog", ret)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(my_prog, qb)
        discard(qb)

    res = main.emulator(n_qubits=2).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
            "my_prog": [0],
        }
    ]
