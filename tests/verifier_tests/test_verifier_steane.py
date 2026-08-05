from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_identity,
        steane.implement_identity,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_single_block_identity_with_shor_extraction() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_identity,
        steane.implement_identity_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )
    assert sem == impl


def test_steane_double_block_identity_with_shor_extraction() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=2,
    )
    assert sem == impl


def test_steane_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_h() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_h,
        steane.implement_h,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_h_with_ancilla() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_h,
        steane.implement_h_with_ancilla,
        code_definition=steane.STEANE_DEF,
        num_ancilla_qubits=1,
    )
    assert sem == impl


def test_steane_s() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_s,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_sdg() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_sdg,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_invalid_s() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_s,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl


def test_steane_invalid_sdg() -> None:
    sem, impl = compute_verification_signterms(
        steane.specify_sdg,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl


def test_steane_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl
