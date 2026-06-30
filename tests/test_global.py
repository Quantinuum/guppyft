import re
from collections.abc import Callable
from typing import no_type_check

import pytest
from guppylang import array, guppy
from guppylang.emulator import EmulatorError
from guppylang.std.builtins import owned, result
from guppylang.std.qsystem.random import RNG
from guppylang.std.quantum import discard, discard_array, measure, qubit, x

from guppyft.globals import map_global, with_global


def run_global_test(
    main_func: Callable[[], None],
    *,
    assert_result: dict[str, list[int]] | None = None,
    n_qubits: int = 1,
) -> None:
    """Fixture to run emulation of a program with global ops."""

    @guppy
    def main() -> None:
        main_func()
        result("smoke", 0)

    if assert_result is None:
        assert_result = {"smoke": [0]}
    else:
        assert "smoke" not in assert_result, "Test configuration: smoke key not allowed"
        assert_result["smoke"] = [0]

    res = main.emulator(n_qubits=n_qubits).run().collated_shots()
    assert res == [assert_result]


def test_with_global_qubit() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog)
        discard(qb)

    run_global_test(main, assert_result={"my_prog": [19]})


def test_with_global_int() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        with_global(0, my_prog)

    run_global_test(main, assert_result={"my_prog": [19]})


def test_with_global_array_int() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        with_global(array(0), my_prog)

    run_global_test(main, assert_result={"my_prog": [19]})


def test_with_global_array_qubit() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        qb_arr = array(qubit())
        qb_arr = with_global(qb_arr, my_prog)
        discard_array(qb_arr)

    run_global_test(main, assert_result={"my_prog": [19]})


def test_with_global_struct() -> None:
    @guppy.struct
    class MyStruct:
        i: int

    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        struct = MyStruct(0)  # type: ignore[call-arg]
        with_global(struct, my_prog)

    run_global_test(main, assert_result={"my_prog": [19]})


def test_global_struct_with_rng() -> None:
    """Including an RNG in the global state is expected to be a common requirement for
    randomised compilation so it is tested explicitly."""

    @guppy.struct
    class MyStruct:
        rng: RNG

        @guppy
        @no_type_check
        def discard(self: "MyStruct" @ owned) -> None:
            self.rng.discard()

    @guppy
    @no_type_check
    def foo(struct: MyStruct @ owned) -> MyStruct:
        result("foo", struct.rng.random_int())
        return struct

    @guppy
    def my_prog() -> None:
        map_global(foo)
        map_global(foo)

    @guppy
    @no_type_check
    def main() -> None:
        struct = MyStruct(RNG(1))
        struct = with_global(struct, my_prog)
        result("main", struct.rng.random_int())
        struct.discard()

    run_global_test(
        main,
        assert_result={
            "foo": [1307692281, -444364974],
            "main": [1491967504],
        },
    )


def test_with_global_input_args() -> None:
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

    run_global_test(main, assert_result={"my_prog": [1, 3, 6]})


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
        result("main", i)
        result("main", j)
        qb, i, j, k = with_global(qb, my_prog2, 1)
        result("main", i)
        result("main", j)
        result("main", k)
        discard(qb)

    run_global_test(
        main,
        assert_result={"my_prog": [1, 2, 3], "main": [2, 2, 3, 2, 3, 4]},
    )


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

    run_global_test(main, assert_result={"main": [1]})


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

    run_global_test(main, assert_result={"main": [1]})


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

    run_global_test(main, assert_result={"main": [1]})


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

    with pytest.raises(
        RuntimeError,
        match=(
            r"Input type does not match global variable type. Found \"{ i1, ptr }\","
            r" Expected \"{ i1, i64 }\""
        ),
    ):
        run_global_test(main)


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
        match=re.escape("Panic (#1001): No global provided for GlobalsOp::With"),
    ):
        run_global_test(main)


def test_nested_with() -> None:
    """Test nested map call i.e. with(with(map(...))).
    The outer global should be independent of the inner.
    `map` should act on the inner global."""

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
        result("arr_inner", arr_inner[0])
        map_global(foo, 2)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global(arr_outer, my_prog)
        result("arr_outer", arr_outer[0])

    run_global_test(
        main,
        assert_result={"arr_inner": [11], "arr_outer": [3]},
    )


def test_nested_map_calls_error() -> None:
    """Test the scenario with(map(map(...))) i.e. nested map calls.
    We expect this to fail as the first `map` call retrieves the global variable, so
    the global will be `None` in the second call"""

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
        match=re.escape("Panic (#1001): No global provided for GlobalsOp::With"),
    ):
        run_global_test(main)


def test_map_return_tuple_type() -> None:
    """Testing returning a tuple as the sole return value from `map`.
    This is to check that the tuple is not unpacked by Guppy.
    The return from map should be `tuple[tuple[int,int]]`."""

    @guppy
    def foo(g: int) -> tuple[int, tuple[int, int]]:
        return g, (g + 1, g + 2)

    @guppy
    def my_prog() -> None:
        res = map_global(foo)  # Returns tuple[tuple[int,int]
        result("my_prog", res[0][0])
        result("my_prog", res[0][1])

    @guppy
    def main() -> None:
        with_global(0, my_prog)

    run_global_test(
        main,
        assert_result={"my_prog": [1, 2]},
    )


def test_with_global_tuple_type() -> None:

    @guppy
    def no_return() -> None:
        pass

    @guppy
    def int_return() -> int:
        return 1

    @guppy
    def tuple_return() -> tuple[int, int]:
        return 2, 3

    @guppy
    def main() -> None:
        with_global((0, 0), no_return)
        _, i = with_global((0, 0), int_return)
        result("int_return", i)
        _, i, j = with_global(
            (0, 0),
            tuple_return,
        )
        result("tuple_return", i)
        result("tuple_return", j)

    run_global_test(main, assert_result={"int_return": [1], "tuple_return": [2, 3]})


def test_map_global_tuple_type() -> None:

    @guppy
    def map_no_return(g: tuple[int, int]) -> tuple[tuple[int, int]]:
        return (g,)

    @guppy
    def map_int_return(g: tuple[int, int]) -> tuple[tuple[int, int], int]:
        return g, 0

    @guppy
    def map_tuple_return(g: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
        return g, (1, 2)

    @guppy
    def my_prog() -> None:
        map_global(map_no_return)
        i = map_global(map_int_return)
        result("map_int_return", i)
        ((i, j),) = map_global(map_tuple_return)
        result("map_tuple_return", i)
        result("map_tuple_return", j)

    @guppy
    def main() -> None:
        with_global((0, 0), my_prog)

    run_global_test(
        main,
        assert_result={
            "map_int_return": [0],
            "map_tuple_return": [
                1,
                2,
            ],
        },
    )
