from guppyft.verifier.verify import (
    valid_clifford_implementation,
    valid_pauli_eigenstate_preparation,
)

from .ops import css_4q


def test_single_block_css_4q_id_verification() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_identity,
        css_4q.implement_identity,
        css_4q.CSS_4Q_DEF,
    )


def test_double_block_css_4q_id() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_identity_double_block,
        css_4q.implement_identity_double_block,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_zero_state() -> None:
    assert valid_pauli_eigenstate_preparation(
        css_4q.specify_zero_state,
        css_4q.implement_non_ft_zero_state,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_plus_state() -> None:
    assert valid_pauli_eigenstate_preparation(
        css_4q.specify_plus_state,
        css_4q.implement_non_ft_plus_state,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_zero_state_not_plus_state() -> None:
    assert not valid_pauli_eigenstate_preparation(
        css_4q.specify_zero_state,
        css_4q.implement_non_ft_plus_state,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_bell_state() -> None:
    assert valid_pauli_eigenstate_preparation(
        css_4q.specify_bell_state,
        css_4q.implement_non_ft_bell_state,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_intrablock_cz() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_intra_block_cz,
        css_4q.implement_intra_block_cz,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_intrablock_cx() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_intra_block_cx,
        css_4q.implement_intra_block_cx,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_addressable_rz_half_pi() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_addressable_rz_half_pi,
        css_4q.implement_addressable_rz_half_pi,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_addressable_rx_half_pi() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_addressable_rx_half_pi,
        css_4q.implement_addressable_rx_half_pi,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_addressable_rx_minus_half_pi() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_addressable_rx_minus_half_pi,
        css_4q.implement_addressable_rx_minus_half_pi,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_addressable_h() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_addressable_h,
        css_4q.implement_addressable_h,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_double_h() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_double_h,
        css_4q.implement_double_h,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_transversal_cx() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_transversal_cx,
        css_4q.implement_transversal_cx,
        css_4q.CSS_4Q_DEF,
    )


def test_css_4q_transversal_zzmax() -> None:
    assert valid_clifford_implementation(
        css_4q.specify_interblock_zzmax,
        css_4q.implement_interblock_zzmax,
        css_4q.CSS_4Q_DEF,
    )
