from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
    compute_verification_signterms_double_block_state,
    compute_verification_signterms_single_block_state,
)

from .ops import iceberg


def test_single_block_iceberg_id_verification() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_identity,
        iceberg.implement_identity,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_double_block_iceberg_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.specify_identity_double_block,
        iceberg.implement_identity_double_block,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_zero_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        iceberg.specify_zero_state,
        iceberg.implement_non_ft_zero_state,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        iceberg.specify_plus_state,
        iceberg.implement_non_ft_plus_state,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_zero_state_not_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        iceberg.specify_zero_state,
        iceberg.implement_non_ft_plus_state,
        iceberg.ICEBERG_DEF,
    )
    assert sem != impl


def test_iceberg_bell_state() -> None:
    sem, impl = compute_verification_signterms_double_block_state(
        iceberg.specify_bell_state,
        iceberg.implement_non_ft_bell_state,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_intrablock_cz() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_intra_block_cz,
        iceberg.implement_intra_block_cz,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_intrablock_cx() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_intra_block_cx,
        iceberg.implement_intra_block_cx,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rz_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_addressable_rz_half_pi,
        iceberg.implement_addressable_rz_half_pi,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rx_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_addressable_rx_half_pi,
        iceberg.implement_addressable_rx_half_pi,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rx_minus_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_addressable_rx_minus_half_pi,
        iceberg.implement_addressable_rx_minus_half_pi,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_h() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_addressable_h,
        iceberg.implement_addressable_h,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_double_h() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.specify_double_h,
        iceberg.implement_double_h,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_transversal_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.specify_transversal_cx,
        iceberg.implement_transversal_cx,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_transversal_zzmax() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.specify_interblock_zzmax,
        iceberg.implement_interblock_zzmax,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl
