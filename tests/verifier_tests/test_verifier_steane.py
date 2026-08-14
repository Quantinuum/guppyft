import pytest

from guppyft.verifier.verify import (
    InvalidImplementationError,
    check_clifford_semantics,
    check_stabilizer_state_semantics,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    check_clifford_semantics(
        steane.specify_identity,
        steane.implement_identity,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_single_block_identity_with_shor_extraction() -> None:
    check_clifford_semantics(
        steane.specify_identity,
        steane.implement_identity_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )


def test_steane_double_block_identity_with_shor_extraction() -> None:
    check_clifford_semantics(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=2,
    )


def test_steane_double_block_identity() -> None:
    check_clifford_semantics(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state() -> None:
    check_stabilizer_state_semantics(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )
    check_stabilizer_state_semantics(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_ft_zero_state() -> None:
    check_stabilizer_state_semantics(
        steane.specify_zero_state,
        steane.implement_ft_zero_state,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=7,
    )


def test_steane_plus_state() -> None:
    check_stabilizer_state_semantics(
        steane.specify_plus_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state_not_plus_state() -> None:
    with pytest.raises(
        InvalidImplementationError,
        match=r"The implementation does not match the specified semantics.",
    ):
        check_stabilizer_state_semantics(
            steane.specify_zero_state,
            steane.implement_non_ft_plus_state,
            code_definition=steane.STEANE_DEF,
        )


def test_steane_bell_state() -> None:
    check_stabilizer_state_semantics(
        steane.specify_bell_state,
        steane.implement_non_ft_bell_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h() -> None:
    check_clifford_semantics(
        steane.specify_h,
        steane.implement_h,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h_with_ancilla() -> None:
    check_clifford_semantics(
        steane.specify_h,
        steane.implement_h_with_ancilla,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )


def test_steane_s() -> None:
    check_clifford_semantics(
        steane.specify_s,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_sdg() -> None:
    check_clifford_semantics(
        steane.specify_sdg,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_invalid_s() -> None:
    with pytest.raises(
        InvalidImplementationError,
        match=r"The implementation does not match the specified semantics.",
    ):
        check_clifford_semantics(
            steane.specify_s,
            steane.implement_sdg,
            code_definition=steane.STEANE_DEF,
        )


def test_steane_invalid_sdg() -> None:
    with pytest.raises(
        InvalidImplementationError,
        match=r"The implementation does not match the specified semantics.",
    ):
        check_clifford_semantics(
            steane.specify_sdg,
            steane.implement_s,
            code_definition=steane.STEANE_DEF,
        )


def test_steane_cx() -> None:
    check_clifford_semantics(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
    )
