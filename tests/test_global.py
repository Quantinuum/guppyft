import re
from typing import no_type_check

import pytest
from guppylang import array, guppy
from guppylang.emulator import EmulatorError
from guppylang.std.builtins import owned, result
from guppylang.std.quantum import discard, measure, qubit, x

from guppyft.globals import map_global_state, with_global_state


def test_with_map() -> None:
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
    def foo(
        qb: qubit,
        i: tuple[int, int],
    ) -> tuple[int, int]:
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
    def foo(qb: qubit) -> None:
        x(qb)

    @guppy
    def main() -> None:
        map_global_state(foo)

    # TODO the error should be more specific
    with pytest.raises(EmulatorError) as _:
        main.emulator(n_qubits=1).run().collated_shots()


def test_nested_with() -> None:
    @guppy
    @no_type_check
    def foo(i: array[int, 1], j: int) -> None:
        i[0] = i[0] + j

    @guppy
    def my_nested_prog() -> None:
        map_global_state(foo, 1)

    @guppy
    def my_prog() -> None:
        map_global_state(foo, 1)
        arr_inner = array(10)
        arr_inner = with_global_state(arr_inner, my_nested_prog)
        result("arr_inner", arr_inner)
        map_global_state(foo, 2)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global_state(arr_outer, my_prog)
        result("arr_outer", arr_outer)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "arr_inner": [[11]],
            "arr_outer": [[3]],
        }
    ]


def test_mismatch_global_type() -> None:
    @guppy
    @no_type_check
    def foo(arr: array[int, 1]) -> int:
        return arr[0]

    @guppy
    def my_prog() -> None:
        map_global_state(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        discard(qb)

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Failed to emit LLVM for function tests.test_global.test_mismatch_global_"
            "type.<locals>.my_prog at node Node(15)"
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
        map_global_state(foo)

    @guppy
    def main() -> None:
        with_global_state(0, my_prog)

    with pytest.raises(
        TypeError, match=r"Global arg must be linear. Found int<6>."
    ) as _:
        main.emulator(n_qubits=1).run().collated_shots()


def test_map_linear_input_no_output() -> None:
    @guppy
    @no_type_check
    def foo(qb: qubit, arr: tuple[qubit]) -> None:
        result("foo", array(0, 1))
        x(qb)

    @guppy
    def my_prog() -> None:
        qb_arr = (qubit(),)
        map_global_state(foo, qb_arr)
        (q0,) = qb_arr
        discard(q0)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        discard(qb)

    res = main.emulator(n_qubits=3).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
        }
    ]


# TODO an additional overload is required to support `@ owned` inputs
@pytest.mark.skip
def test_map_linear_owned_input_no_output() -> None:
    @guppy
    @no_type_check
    def foo(qb: qubit, qb_in: qubit @ owned) -> None:
        result("foo", array(0, 1))
        x(qb)
        discard(qb_in)

    @guppy
    def my_prog() -> None:
        map_global_state(foo, qubit())

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        discard(qb)

    res = main.emulator(n_qubits=3).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
        }
    ]


def test_map_linear_input_nonlinear_output() -> None:
    @guppy
    @no_type_check
    def foo(qb: qubit, arr: array[int, 2]) -> int:
        result("foo", arr)
        x(qb)
        return 0

    @guppy
    def my_prog() -> None:
        ret = map_global_state(foo, array(0, 1))
        result("my_prog", ret)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        discard(qb)

    res = main.emulator(n_qubits=2).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
            "my_prog": [0],
        }
    ]


def test_map_linear_input_linear_output() -> None:
    @guppy
    @no_type_check
    def foo(qb: qubit, arr: array[int, 2]) -> qubit:
        result("foo", arr)
        x(qb)
        return qubit()

    @guppy
    def my_prog() -> None:
        ret = map_global_state(foo, array(0, 1))
        result("my_prog", measure(ret))

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global_state(qb, my_prog)
        discard(qb)

    res = main.emulator(n_qubits=2).run().collated_shots()

    assert res == [
        {
            "foo": [[0, 1]],
            "my_prog": [0],
        }
    ]
