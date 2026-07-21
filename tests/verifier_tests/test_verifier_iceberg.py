from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import iceberg


def test_single_block_iceberg_id_verification() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.logical_identity,
        iceberg.physical_identity,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_double_block_iceberg_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.logical_identity_double_block,
        iceberg.physical_identity_double_block,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_intrablock_cz() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.intra_block_cz_logical,
        iceberg.intra_block_cz_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_intrablock_cx() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.intra_block_cx_logical,
        iceberg.intra_block_cx_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rz_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.addressable_rz_half_pi_logical,
        iceberg.addressable_rz_half_pi_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rx_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.addressable_rx_half_pi_logical,
        iceberg.addressable_rx_half_pi_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_rx_minus_half_pi() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.addressable_rx_minus_half_pi_logical,
        iceberg.addressable_rx_minus_half_pi_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_addressable_h() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.addressable_h_logical,
        iceberg.addressable_h_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_double_h() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.double_h_logical,
        iceberg.double_h_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_transversal_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.transversal_cx_logical,
        iceberg.transversal_cx_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_iceberg_transversal_zzmax() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.interblock_zzmax_logical,
        iceberg.interblock_zzmax_physical,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl
