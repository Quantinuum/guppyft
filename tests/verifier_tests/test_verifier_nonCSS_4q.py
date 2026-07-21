from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import nonCSS_4q


def test_single_block_nonCSS_4q_id() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_identity,
        nonCSS_4q.physical_identity,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_double_block_nonCSS_4q_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_4q.logical_identity_double_block,
        nonCSS_4q.physical_identity_double_block,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row1() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_row1,
        nonCSS_4q.physical_row1,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row2() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_row2,
        nonCSS_4q.physical_row2,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row3() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_row3,
        nonCSS_4q.physical_row3,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row4() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_row4,
        nonCSS_4q.physical_row4_incorrect,
        nonCSS_4q.CODE_DEF,
    )
    assert sem != impl

    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_row4,
        nonCSS_4q.physical_row4_correct,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_intra_cz() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.logical_intra_cz,
        nonCSS_4q.physical_intra_cz,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl
