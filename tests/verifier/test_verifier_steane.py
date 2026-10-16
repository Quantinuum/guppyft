from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.array import ArrayIter
from guppylang.std.builtins import array, owned
from guppylang.std.iter import SizedIter
from guppylang.std.quantum import qubit
from guppylang_internals.error import GuppyError

from guppyft.verify import (
    valid_clifford_implementation,
    valid_stabilizer_state_preparation,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity,
        steane.implement_identity,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_single_block_identity_with_shor_extraction() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity,
        steane.implement_identity_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        n_impl_ancillas=1,
    )


def test_steane_double_block_identity_with_shor_extraction() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        n_impl_ancillas=2,
    )


def test_steane_double_block_identity() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state_logical_block() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state_logical_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_ft_zero_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_ft_zero_state,
        code_definition=steane.STEANE_DEF,
        n_impl_ancillas=7,
    )


def test_steane_plus_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_plus_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state_not_plus_state() -> None:
    assert not valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_bell_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_bell_state,
        steane.implement_non_ft_bell_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h() -> None:
    assert valid_clifford_implementation(
        steane.specify_h,
        steane.implement_h,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h_logical_block() -> None:
    assert valid_clifford_implementation(
        steane.specify_h,
        steane.implement_h_logical_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h_with_ancilla() -> None:
    assert valid_clifford_implementation(
        steane.specify_h,
        steane.implement_h_with_ancilla,
        code_definition=steane.STEANE_DEF,
        n_impl_ancillas=1,
    )


def test_steane_s() -> None:
    assert valid_clifford_implementation(
        steane.specify_s,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_sdg() -> None:
    assert valid_clifford_implementation(
        steane.specify_sdg,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_invalid_s() -> None:
    assert not valid_clifford_implementation(
        steane.specify_s,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_invalid_sdg() -> None:
    assert not valid_clifford_implementation(
        steane.specify_sdg,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_cx() -> None:
    assert valid_clifford_implementation(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_cx_logical_block() -> None:
    assert valid_clifford_implementation(
        steane.specify_cx,
        steane.implement_cx_logical_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state_unsupported_iterable_struct() -> None:
    @guppy.struct
    class UnsupportedBlock:
        data_qs: array[qubit, 7]  # type: ignore[valid-type]

        @guppy
        @no_type_check
        def __iter__(
            self: "UnsupportedBlock" @ owned,
        ) -> SizedIter[ArrayIter[qubit, 7], 7]:
            return self.data_qs.__iter__()

    @guppy
    @no_type_check
    def implement_non_ft_zero_unsupported_block() -> UnsupportedBlock:
        return UnsupportedBlock(steane.implement_non_ft_zero_state())

    with pytest.raises(
        GuppyError,
        match="Invalid call of overloaded function",
    ) as error:
        valid_stabilizer_state_preparation(
            steane.specify_zero_state,
            implement_non_ft_zero_unsupported_block,
            code_definition=steane.STEANE_DEF,
        )

    assert "UnsupportedBlock" in str(error.value)


def test_steane_bell_state_logical_block() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_bell_state,
        steane.implement_bell_state_logical_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h_logical_block_is_not_identity() -> None:
    assert not valid_clifford_implementation(
        steane.specify_identity,
        steane.implement_h_logical_block,
        code_definition=steane.STEANE_DEF,
    )
