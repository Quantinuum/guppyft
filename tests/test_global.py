import re
from typing import no_type_check

import pytest
from guppylang import array, guppy
from guppylang.emulator import EmulatorError
from guppylang.std.builtins import owned, result
from guppylang.std.quantum import discard, measure, qubit, x

from guppyft.globals import map_global, with_global


def test_with_global_linear() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog)
        discard(qb)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"my_prog": [19]}]


def test_with_global_non_linear() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        with_global(1, my_prog)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"my_prog": [19]}]


def test_with_non_linear_inputs() -> None:
    @guppy
    def my_prog0(i: int) -> None:
        result("my_prog", i)

    @guppy
    def my_prog1(i: int, j: int) -> None:
        result("my_prog", i + j)

    @guppy
    def my_prog2(i: int, j: int, k: int) -> None:
        result("my_prog", i + j + k)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog0, 1)
        qb = with_global(qb, my_prog1, 1, 2)
        qb = with_global(qb, my_prog2, 1, 2, 3)
        discard(qb)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"my_prog": [1, 3, 6]}]


def test_with_outputs() -> None:
    @guppy
    def my_prog0(i: int) -> int:
        result("my_prog", i)
        return i + 1

    @guppy
    def my_prog1(i: int) -> tuple[int, int]:
        result("my_prog", 2 * i)
        return i + 1, i + 2

    @guppy
    def my_prog2(i: int) -> tuple[int, int, int]:
        result("my_prog", 3 * i)
        return i + 1, i + 2, i + 3

    @guppy
    def main() -> None:
        qb = qubit()
        qb, i = with_global(qb, my_prog0, 1)
        result("main", i)
        qb, i, j = with_global(qb, my_prog1, 1)
        result("main", array(i, j))
        qb, i, j, k = with_global(qb, my_prog2, 1)
        result("main", array(i, j, k))
        discard(qb)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"my_prog": [1, 2, 3], "main": [2, [2, 3], [2, 3, 4]]}]


def test_with_owned_input() -> None:
    @guppy
    @no_type_check
    def my_prog(qb: qubit @ owned) -> qubit:
        x(qb)
        return qb

    @guppy
    def main() -> None:
        qb = qubit()
        r: tuple[int, qubit] = with_global(1, my_prog, qb)
        result("main", measure(r[1]).read())

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"main": [1]}]


def test_map_global_linear() -> None:
    @guppy
    @no_type_check
    def foo(qb: qubit @ owned) -> qubit:
        x(qb)
        return qb

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog)
        result("main", measure(qb).read())

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"main": [1]}]


def test_map_global_linear_return_arg_order_error() -> None:
    @guppy
    def foo(qb: qubit @ owned) -> tuple[int, qubit]:  # type: ignore[valid-type]
        x(qb)
        return 0, qb

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog)
        result("main", measure(qb).read())

    with pytest.raises(AssertionError):
        main.compile()


# TODO fix test
@pytest.mark.skip
def test_map_missing_global_arg_input_error() -> None:
    @guppy
    def foo() -> int:
        return 0

    @guppy
    def my_prog() -> None:
        map_global(foo)  # type: ignore[call-overload]

    my_prog.compile()


def test_map_global_non_linear() -> None:
    @guppy
    def foo(i: int) -> int:
        i = i + 1
        return i

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        i = 0
        i = with_global(i, my_prog)
        result("main", i)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [{"main": [1]}]


def test_map_mismatch_global_return_type_error() -> None:
    @guppy
    def foo(i: float) -> int:
        return i  # type: ignore[return-value]

    @guppy
    def my_prog() -> None:
        map_global(foo)

    with pytest.raises(AssertionError):
        my_prog.compile()


def test_with_map_mismatch_global_type_error() -> None:
    @guppy
    def foo(i: int) -> int:
        return i

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        with_global("", my_prog)

    # TODO match more specific error
    with pytest.raises(RuntimeError):
        main.emulator(n_qubits=1).run().collated_shots()


def test_map_without_with() -> None:
    @guppy
    def foo(i: int) -> int:
        result("foo", i)
        return i - 1

    @guppy
    def main() -> None:
        map_global(foo)

    with pytest.raises(
        EmulatorError,
        match=re.escape("Panic (#11001): No global provided for GlobalsOp::With"),
    ):
        main.emulator(n_qubits=1).run().collated_shots()


def test_nested_with() -> None:
    @guppy
    @no_type_check
    def foo(i: array[int, 1] @ owned, j: int) -> array[int, 1]:
        i[0] = i[0] + j
        return i

    @guppy
    def my_nested_prog() -> None:
        map_global(foo, 1)

    @guppy
    def my_prog() -> None:
        map_global(foo, 1)
        arr_inner = array(10)
        arr_inner = with_global(arr_inner, my_nested_prog)
        result("arr_inner", arr_inner)
        map_global(foo, 2)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global(arr_outer, my_prog)
        result("arr_outer", arr_outer)

    res = main.emulator(n_qubits=1).run().collated_shots()
    assert res == [
        {
            "arr_inner": [[11]],
            "arr_outer": [[3]],
        }
    ]


def test_nested_map_calls_error() -> None:
    @guppy
    def bar(i: int) -> int:
        return i

    @guppy
    def foo(i: int) -> int:
        map_global(bar)
        return i

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        with_global(0, my_prog)

    with pytest.raises(
        EmulatorError,
        match=re.escape("Panic (#11001): No global provided for GlobalsOp::With"),
    ):
        main.emulator(n_qubits=1).run().collated_shots()


def test_map_return_tuple_type() -> None:
    @guppy
    def foo(g: int) -> tuple[int, tuple[int, int]]:
        return g, (0, 0)

    @guppy
    def my_prog() -> None:
        map_global(foo)

    @guppy
    def main() -> None:
        with_global(0, my_prog)

    main.emulator(n_qubits=1).run().collated_shots()
