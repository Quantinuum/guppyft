from guppyft.verifier.verify import (
    check_clifford_semantics,
    check_stabilizer_state_semantics,
)

from .ops import nonCSS_5q


def test_single_block_nonCSS_5q_id() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_identity,
        nonCSS_5q.implement_identity,
        nonCSS_5q.CODE_DEF,
    )


def test_double_block_nonCSS_5q_id() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_identity_double_block,
        nonCSS_5q.implement_identity_double_block,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_zero_state() -> None:
    assert check_stabilizer_state_semantics(
        nonCSS_5q.specify_zero_state,
        nonCSS_5q.implement_non_ft_zero_state,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_plus_state() -> None:
    assert check_stabilizer_state_semantics(
        nonCSS_5q.specify_plus_state,
        nonCSS_5q.implement_non_ft_plus_state,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_zero_state_not_plus_state() -> None:
    assert not check_stabilizer_state_semantics(
        nonCSS_5q.specify_zero_state,
        nonCSS_5q.implement_non_ft_plus_state,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_bell_state() -> None:
    assert check_stabilizer_state_semantics(
        nonCSS_5q.specify_bell_state,
        nonCSS_5q.implement_non_ft_bell_state,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_k() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_k,
        nonCSS_5q.implement_k,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_kdg() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_kdg,
        nonCSS_5q.implement_kdg,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_different_k() -> None:
    assert not check_clifford_semantics(
        nonCSS_5q.specify_k,
        nonCSS_5q.implement_kdg,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_h() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_h,
        nonCSS_5q.implement_h,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_k_not_h() -> None:
    assert not check_clifford_semantics(
        nonCSS_5q.specify_h,
        nonCSS_5q.implement_k,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_cz() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_cz,
        nonCSS_5q.implement_cz,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_cx() -> None:
    assert check_clifford_semantics(
        nonCSS_5q.specify_cx,
        nonCSS_5q.implement_cx,
        nonCSS_5q.CODE_DEF,
    )


def test_nonCSS_5q_cz_not_cx() -> None:
    assert not check_clifford_semantics(
        nonCSS_5q.specify_cz,
        nonCSS_5q.implement_cx,
        nonCSS_5q.CODE_DEF,
    )
