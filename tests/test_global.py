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


def run_global_smoke_test(
    *,
    main_func: Callable[[], None],
    expected_res: dict[str, list[int]] | None = None,
    n_qubits: int = 1,
) -> None:

    @guppy
    def main() -> None:
        main_func()
        result("smoke", 0)

    if expected_res is None:
        expected_res = {"smoke": [0]}
    else:
        expected_res["smoke"] = [0]

    res = main.emulator(n_qubits=n_qubits).run().collated_shots()
    assert len(res) == 1
    assert res[0] == expected_res


def test_with_global_qubit() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        qb = qubit()
        qb = with_global(qb, my_prog)
        discard(qb)

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [19]})


def test_with_global_int() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        with_global(0, my_prog)

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [19]})


def test_with_global_array_int() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        with_global(array(0), my_prog)

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [19]})


def test_with_global_array_qubit() -> None:
    @guppy
    def my_prog() -> None:
        result("my_prog", 19)

    @guppy
    def main() -> None:
        qb_arr = array(qubit())
        qb_arr = with_global(qb_arr, my_prog)
        discard_array(qb_arr)

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [19]})


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

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [19]})


# Test global struct with qsystem RNG
def test_global_struct_with_rng() -> None:
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

    run_global_smoke_test(
        main_func=main,
        expected_res={
            "foo": [1307692281, -444364974],
            "main": [1491967504],
        },
    )


# Test `with_global` with input args
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

    run_global_smoke_test(main_func=main, expected_res={"my_prog": [1, 3, 6]})


# Test `with_global` outputs
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

    run_global_smoke_test(
        main_func=main,
        expected_res={"my_prog": [1, 2, 3], "main": [2, 2, 3, 2, 3, 4]},
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

    run_global_smoke_test(main_func=main, expected_res={"main": [1]})


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

    run_global_smoke_test(main_func=main, expected_res={"main": [1]})


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

    run_global_smoke_test(main_func=main, expected_res={"main": [1]})


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
    with pytest.raises(
        RuntimeError,
        match=(
            r"Input type does not match global variable type. Found \"{ i1, ptr }\","
            r" Expected \"{ i1, i64 }\""
        ),
    ):
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
        match=re.escape("Panic (#1001): No global provided for GlobalsOp::With"),
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
        result("arr_inner", arr_inner[0])
        map_global(foo, 2)

    @guppy
    def main() -> None:
        arr_outer = array(0)
        arr_outer = with_global(arr_outer, my_prog)
        result("arr_outer", arr_outer[0])

    run_global_smoke_test(
        main_func=main,
        expected_res={"arr_inner": [11], "arr_outer": [3]},
    )


# Test the scenario with(map(map(..))) i.e. nested map calls
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
        match=re.escape("Panic (#1001): No global provided for GlobalsOp::With"),
    ):
        main.emulator(n_qubits=1).run().collated_shots()


def test_map_return_tuple_type() -> None:
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

    run_global_smoke_test(
        main_func=main,
        expected_res={"my_prog": [1, 2]},
    )
