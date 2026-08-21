from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.lang import comptime, owned
from guppylang.std.mem import with_owned
from guppylang.std.quantum import qubit, x, z

from guppyft.code.steane.primitives import (
    knill_qec_cycle,
    prep_zero_non_ft,
    steane_x_qec_cycle,
    steane_z_qec_cycle,
)
from guppyft.code.util import LogicalBlock
from guppyft.code_def import StabilizerCode
from guppyft.verifier import valid_clifford_implementation

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
    def knill_qec(block: array[qubit, 7] @ owned) -> tuple[int, array[qubit, 7]]:
        steane_block = LogicalBlock(block)
        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(steane_block, a0, a1)
        block = array(q for q in steane_block.data_qs)
        # Int return is required due to bug in guppy compiler
        # See: https://github.com/Quantinuum/guppylang/issues/2197
        return 0, block

    # The function is expected to borrow the array of qubits,
    # but ownership is required to create a LogicalBlock. Using
    # `with_owned` solves this.
    @guppy
    @no_type_check
    def impl_func(block: array[qubit, 7]) -> None:
        with_owned(block, knill_qec)

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
    def knill_qec(block: array[qubit, 7] @ owned) -> tuple[int, array[qubit, 7]]:
        steane_block = LogicalBlock(block)
        _apply_error(steane_block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(steane_block, a0, a1)
        block = array(q for q in steane_block.data_qs)
        # Int return is required due to bug in guppy compiler
        # See: https://github.com/Quantinuum/guppylang/issues/2197
        return 0, block

    # The function is expected to borrow the array of qubits,
    # but ownership is required to create a LogicalBlock. Using
    # `with_owned` solves this.
    @guppy
    @no_type_check
    def impl_func(block: array[qubit, 7]) -> None:
        with_owned(block, knill_qec)

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=14,
    )


def test_steane_qec_without_errors() -> None:

    @guppy
    @no_type_check
    def steane_qec(block: array[qubit, 7] @ owned) -> tuple[int, array[qubit, 7]]:
        steane_block = LogicalBlock(block)
        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(steane_block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(steane_block, a0)
        block = array(q for q in steane_block.data_qs)
        # Int return is required due to bug in guppy compiler
        # See: https://github.com/Quantinuum/guppylang/issues/2197
        return 0, block

    # The function is expected to borrow the array of qubits,
    # but ownership is required to create a LogicalBlock. Using
    # `with_owned` solves this.
    @guppy
    @no_type_check
    def impl_func(block: array[qubit, 7]) -> None:
        with_owned(block, steane_qec)

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
    def steane_qec(block: array[qubit, 7] @ owned) -> tuple[int, array[qubit, 7]]:
        steane_block = LogicalBlock(block)
        _apply_error(steane_block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(steane_block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(steane_block, a0)
        block = array(q for q in steane_block.data_qs)
        # Int return is required due to bug in guppy compiler
        # See: https://github.com/Quantinuum/guppylang/issues/2197
        return 0, block

    # The function is expected to borrow the array of qubits,
    # but ownership is required to create a LogicalBlock. Using
    # `with_owned` solves this.
    @guppy
    @no_type_check
    def impl_func(block: array[qubit, 7]) -> None:
        with_owned(block, steane_qec)

    assert valid_clifford_implementation(
        specify_identity,
        impl_func,
        code_definition=STEANE_DEF,
        impl_num_ancillas=7,
    )
