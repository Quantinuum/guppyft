from typing import Any, no_type_check

import pytest
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array
from guppylang.std.lang import comptime
from guppylang.std.platform import output
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg, x, y, z

from guppyft.code.steane import primitives as steane_primitives
from guppyft.code.steane.primitives import (
    LogicalBlock,
    _measure_syndromes,
    knill_qec_cycle,
    prep_zero_non_ft,
    steane_x_qec_cycle,
    steane_z_qec_cycle,
)
from guppyft.code_def import StabilizerCode
from guppyft.verify import valid_clifford_implementation

STEANE_DEF = StabilizerCode.from_python_strings(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
    x_logicals=["XXXXXXX"],
    z_logicals=["ZZZZZZZ"],
)


@guppy
@no_type_check
def specify_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def _apply_error(block: LogicalBlock[7], loc: int, is_x_error: bool) -> None:
    if is_x_error:
        x(block.data_qs[loc])
    else:
        z(block.data_qs[loc])


def test_knill_qec_without_errors() -> None:

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))

        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(block, a0, a1)

        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=14,
    )


@pytest.mark.parametrize("error_loc", [0, 1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("is_x_error", [True, False])
def test_knill_qec_with_errors(error_loc: int, is_x_error: bool) -> None:

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))

        _apply_error(block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(block, a0, a1)

        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=14,
    )


def test_steane_qec_without_errors() -> None:

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))

        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(block, a0)

        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=7,
    )


@pytest.mark.parametrize("error_loc", [0, 1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("is_x_error", [True, False])
def test_steane_qec_with_errors(error_loc: int, is_x_error: bool) -> None:

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))

        _apply_error(block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(block, a0)

        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=7,
    )


def test_steane_measure_syndromes() -> None:
    # Note: While `_measure_syndromes` is a private function, it is used
    # as part of magic state preparation which is non-Clifford and not
    # exhaustively tested. This test is included to validate the Clifford
    # components on its own.

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))

        _measure_syndromes(block)

        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(
        specify_identity, impl_func, STEANE_DEF, impl_num_ancillas=3
    )


@pytest.mark.parametrize(
    ("specify_def", "implement_def"),
    [
        (x, steane_primitives.x),
        (y, steane_primitives.y),
        (z, steane_primitives.z),
        (h, steane_primitives.h),
        (s, steane_primitives.s),
        (sdg, steane_primitives.sdg),
    ],
)
def test_steane_1q_primitives(
    specify_def: GuppyFunctionDefinition[[Any], None],
    implement_def: GuppyFunctionDefinition[[Any], None],
) -> None:

    @guppy
    @no_type_check
    def specify_func(q: array[qubit, 1]) -> None:
        specify_def(q[0])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 7]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(7)))
        implement_def(block)
        for i in range(7):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    assert valid_clifford_implementation(specify_func, impl_func, STEANE_DEF)


@pytest.mark.parametrize(
    ("specify_def", "implement_def"),
    [
        (cx, steane_primitives.cx),
        (cz, steane_primitives.cz),
    ],
)
def test_steane_2q_primitives(
    specify_def: GuppyFunctionDefinition[[Any], None],
    implement_def: GuppyFunctionDefinition[[Any], None],
) -> None:

    @guppy
    @no_type_check
    def specify_func(q0: array[qubit, 1], q1: array[qubit, 1]) -> None:
        specify_def(q0[0], q1[0])

    @guppy
    @no_type_check
    def impl_func(arr0: array[qubit, 7], arr1: array[qubit, 7]) -> None:
        blk0 = LogicalBlock(array(arr0.take(i) for i in range(7)))
        blk1 = LogicalBlock(array(arr1.take(i) for i in range(7)))

        implement_def(blk0, blk1)

        for i in range(7):
            arr0.put(blk0.data_qs.take(i), i)
            arr1.put(blk1.data_qs.take(i), i)
        blk0.discard()
        blk1.discard()

    assert valid_clifford_implementation(specify_func, impl_func, STEANE_DEF)


def test_t_gate() -> None:

    @guppy
    def test() -> None:
        blk = steane_primitives.prep_zero_non_ft()
        steane_primitives.h(blk)
        for _ in range(4):
            a = steane_primitives.prep_t_state_ft().force_check().unwrap()
            steane_primitives.inject_t(blk, a)
        steane_primitives.h(blk)
        res = steane_primitives.measure_z(blk)
        output("res", steane_primitives.decode(res))

    res = test.emulator(n_qubits=20).run().collated_shots()

    assert res == [{"res": [1]}]
