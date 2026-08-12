import pytest

from guppyft.verifier.verify import (
    BlockType,
    InvalidImplementationError,
    check_clifford_semantics,
    compute_verification_signterms_double_block_state,
    compute_verification_signterms_double_block_unitary,
    compute_verification_signterms_single_block_state,
    compute_verification_signterms_single_block_unitary,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_identity,
        steane.implement_identity,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_single_block_identity_with_shor_extraction() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_identity,
        steane.implement_identity_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )
    assert sem == impl


def test_steane_double_block_identity_with_shor_extraction() -> None:
    sem, impl = compute_verification_signterms_double_block_unitary(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=2,
    )
    assert sem == impl


def test_steane_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block_unitary(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_zero_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_ft_zero_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        steane.specify_zero_state,
        steane.implement_ft_zero_state,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=7,
    )
    assert sem == impl


def test_steane_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        steane.specify_plus_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_zero_state_not_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        steane.specify_zero_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )
    assert sem != impl


def test_steane_bell_state() -> None:
    sem, impl = compute_verification_signterms_double_block_state(
        steane.specify_bell_state,
        steane.implement_non_ft_bell_state,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_h() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_h,
        steane.implement_h,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_h_with_ancilla() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_h,
        steane.implement_h_with_ancilla,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )
    assert sem == impl


def test_steane_s() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_s,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_sdg() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_sdg,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_invalid_s() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_s,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl


def test_steane_invalid_sdg() -> None:
    sem, impl = compute_verification_signterms_single_block_unitary(
        steane.specify_sdg,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl
    with pytest.raises(
        InvalidImplementationError,
        match=r"The implementation does not match the specified semantics.",
    ):
        check_clifford_semantics(
            steane.specify_sdg,
            steane.implement_s,
            code_definition=steane.STEANE_DEF,
            block_type=BlockType.SingleBlock,
        )


def test_steane_cx() -> None:
    sem, impl = compute_verification_signterms_double_block_unitary(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl

    check_clifford_semantics(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
        block_type=BlockType.DoubleBlock,
    )
