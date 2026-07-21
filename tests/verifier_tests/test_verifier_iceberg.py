from guppyft.verifier.expansion import (
    expand_logical_signterms,
    get_expanded_stabilizer_set,
    pad_code_stabilizers,
)
from guppyft.verifier.verify import (
    compute_stabilizers_double_block,
    compute_stabilizers_single_block,
    compute_verification_signterms,
    compute_verification_signterms_double_block,
    identity_code,
)

from .ops import iceberg


def test_compute_stabilizers_single_block_iceberg_id() -> None:
    choi_stabilizers_before_expansion = compute_stabilizers_single_block(
        identity_code(2), iceberg.logical_identity, 2
    )
    assert (
        str(choi_stabilizers_before_expansion)
        == "(+1, X0 X2), (+1, Z0 Z2), (+1, X1 X3), (+1, Z1 Z3)"
    )

    expanded = expand_logical_signterms(
        choi_stabilizers_before_expansion, iceberg.ICEBERG_DEF
    )
    assert (
        str(expanded)
        == "(+1, X0 X1 X4 X5), (+1, Z1 Z3 Z5 Z7), (+1, X0 X2 X4 X6), (+1, Z2 Z3 Z6 Z7)"
    )

    padded = pad_code_stabilizers(iceberg.ICEBERG_DEF, num_blocks=1)
    assert str(padded) == "X0 X1 X2 X3, Z0 Z1 Z2 Z3, X4 X5 X6 X7, Z4 Z5 Z6 Z7"
    expanded_stabilizer_state_stabilizers = get_expanded_stabilizer_set(
        choi_stabilizers_before_expansion, iceberg.ICEBERG_DEF, num_blocks=1
    )
    assert (
        str(expanded_stabilizer_state_stabilizers)
        == "(+1, X0 X1 X4 X5), (+1, Z1 Z3 Z5 Z7), (+1, X0 X2 X4 X6), (+1, Z2 Z3 Z6 Z7),"
        + " (+1, X0 X1 X2 X3), (+1, Z0 Z1 Z2 Z3), (+1, X4 X5 X6 X7), (+1, Z4 Z5 Z6 Z7)"
    )


def test_single_block_iceberg_id_verification() -> None:
    sem, impl = compute_verification_signterms(
        iceberg.logical_identity,
        iceberg.physical_identity,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_compute_stabilizers_double_block_iceberg_id() -> None:
    choi_stabilizers_before_expansion = compute_stabilizers_double_block(
        identity_code(2),
        iceberg.logical_identity_double_block,
        4,
    )
    assert (
        str(choi_stabilizers_before_expansion)
        == "(+1, X0 X2), (+1, Z0 Z2), (+1, X1 X3), (+1, Z1 Z3),"
        + " (+1, X4 X6), (+1, Z4 Z6), (+1, X5 X7), (+1, Z5 Z7)"
    )
    expanded = expand_logical_signterms(
        choi_stabilizers_before_expansion, iceberg.ICEBERG_DEF
    )
    assert (
        str(expanded)
        == "(+1, X0 X1 X4 X5), (+1, Z1 Z3 Z5 Z7), (+1, X0 X2 X4 X6), (+1, Z2 Z3 Z6 Z7),"
        + " (+1, X8 X9 X12 X13), (+1, Z9 Z11 Z13 Z15), (+1, X8 X10 X12 X14), (+1, Z10 Z11 Z14 Z15)"  # noqa: E501
    )


def test_double_block_iceberg_id() -> None:
    sem, impl = compute_verification_signterms_double_block(
        iceberg.logical_identity_double_block,
        iceberg.physical_identity_double_block,
        iceberg.ICEBERG_DEF,
    )
    assert sem == impl


def test_compute_stabilizers_intrablock_cx_iceberg() -> None:
    choi_stabilizers_before_expansion = compute_stabilizers_single_block(
        identity_code(2),
        iceberg.intra_block_cx_logical,
        2,
    )
    assert (
        str(choi_stabilizers_before_expansion)
        == "(+1, X0 X2 X3), (+1, Z0 Z2), (+1, X1 X3), (+1, Z1 Z2 Z3)"
    )
    expanded = expand_logical_signterms(
        choi_stabilizers_before_expansion, iceberg.ICEBERG_DEF
    )
    assert (
        str(expanded)
        == "(+1, X0 X1 X5 X6), (+1, Z1 Z3 Z5 Z7), (+1, X0 X2 X4 X6), (+1, Z2 Z3 Z5 Z6)"
    )


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
