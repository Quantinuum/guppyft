from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import nonCSS_5q


def test_single_block_nonCSS_5q_id() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_identity,
        nonCSS_5q.physical_identity,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_double_block_nonCSS_5q_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_5q.logical_identity_double_block,
        nonCSS_5q.physical_identity_double_block,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_k() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_k,
        nonCSS_5q.physical_k,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_kdg() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_kdg,
        nonCSS_5q.physical_kdg,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_different_k() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_k,
        nonCSS_5q.physical_kdg,
        nonCSS_5q.CODE_DEF,
    )
    assert sem != impl


def test_nonCSS_5q_h() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_h,
        nonCSS_5q.physical_h,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_k_not_h() -> None:
    sem, impl = compute_verification_signterms(
        nonCSS_5q.logical_h,
        nonCSS_5q.physical_k,
        nonCSS_5q.CODE_DEF,
    )
    assert sem != impl


def test_nonCSS_5q_cz() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_5q.logical_cz,
        nonCSS_5q.physical_cz,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_5q.logical_cx,
        nonCSS_5q.physical_cx,
        nonCSS_5q.CODE_DEF,
    )
    assert sem == impl


def test_nonCSS_5q_cz_not_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        nonCSS_5q.logical_cz,
        nonCSS_5q.physical_cx,
        nonCSS_5q.CODE_DEF,
    )
    assert sem != impl
