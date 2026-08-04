from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
    compute_verification_signterms_single_block_state,
)

from .ops import nonCSS_4q


def test_single_block_nonCSS_4q_id() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_identity,
        nonCSS_4q.implement_identity,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_double_block_nonCSS_4q_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_4q.specify_identity_double_block,
        nonCSS_4q.implement_identity_double_block,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_zero_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        nonCSS_4q.specify_zero_state,
        nonCSS_4q.implement_non_ft_zero_state,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        nonCSS_4q.specify_plus_state,
        nonCSS_4q.implement_non_ft_plus_state,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_zero_state_not_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        nonCSS_4q.specify_zero_state,
        nonCSS_4q.implement_non_ft_plus_state,
        nonCSS_4q.CODE_DEF,
    )
    assert sem != impl


def test_nonCSS_4q_row1() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_row1,
        nonCSS_4q.implement_row1,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row2() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_row2,
        nonCSS_4q.implement_row2,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row3() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_row3,
        nonCSS_4q.implement_row3,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_row4() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_row4,
        nonCSS_4q.implement_row4_incorrect,
        nonCSS_4q.CODE_DEF,
    )
    assert sem != impl

    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_row4,
        nonCSS_4q.implement_row4_correct,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_4q_intra_cz() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_4q.specify_intra_cz,
        nonCSS_4q.implement_intra_cz,
        nonCSS_4q.CODE_DEF,
    )
    assert sem == impl
