from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_identity,
        steane.physical_identity,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.logical_identity_double_block,
        steane.physical_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_h() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_h,
        steane.physical_h,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_s() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_s,
        steane.physical_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_sdg() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_sdg,
        steane.physical_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_steane_invalid_s() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_s,
        steane.physical_sdg,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl


def test_steane_invalid_sdg() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_sdg,
        steane.physical_s,
        code_definition=steane.STEANE_DEF,
    )

    assert sem != impl


def test_steane_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.logical_cx,
        steane.physical_cx,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl
