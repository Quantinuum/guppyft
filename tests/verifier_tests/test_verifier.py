import numpy as np
from zixy.qubit import pauli

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

from .ops import bitflip, iceberg, steane


def test_bell_state_stabilizers() -> None:
    stabilizer_terms = compute_stabilizers_single_block(
        identity_code(1), steane.logical_identity, 1
    )
    assert str(stabilizer_terms) == "(+1, X0 X1), (+1, Z0 Z1)"


def test_s_state_stabilizers() -> None:
    terms_logical = compute_stabilizers_single_block(
        identity_code(1), steane.logical_s, 1
    )

    terms_physical = compute_stabilizers_single_block(
        steane.STEANE_DEF, steane.physical_s, 7
    )

    assert str(terms_logical) == "(+1, X0 Y1), (+1, Z0 Z1)"
    assert len(terms_physical) == 14


LOGICAL_STRINGSET = pauli.StringSet.from_cmpnts(pauli.Strings.from_str("X0 X1, Z0 Z1"))


def test_padding() -> None:
    padded_steane_stabilizers = pad_code_stabilizers(steane.STEANE_DEF, num_blocks=1)
    assert len(padded_steane_stabilizers) == 2 * (7 - 1)
    for g_tuple in padded_steane_stabilizers.to_strings().get_tuples():
        assert len(g_tuple) == 2 * 7


def test_logical_expansion() -> None:
    expanded_logicals = expand_logical_signterms(
        LOGICAL_STRINGSET.to_strings().into(pauli.SignTerms), steane.STEANE_DEF
    )
    expanded_tuples = expanded_logicals.strings.get_tuples()
    zs = tuple([pauli.PauliMatrix.Z] * 14)
    xs = tuple([pauli.PauliMatrix.X] * 14)
    assert expanded_tuples == (xs, zs)


def test_entire_stabilizer_set() -> None:
    stab_set = get_expanded_stabilizer_set(
        LOGICAL_STRINGSET.to_strings().into(pauli.SignTerms),
        steane.STEANE_DEF,
        num_blocks=1,
    )
    assert len(stab_set.strings.get_tuples()) == 14

    # assert that all Pauli strings in stab_set commute with one another.
    assert np.all(stab_set.strings.compatibility_matrix()) == 1


def test_steane_h() -> None:
    sem, impl = compute_verification_signterms(
        steane.logical_h,
        steane.physical_h,
        code_definition=steane.STEANE_DEF,
    )

    assert sem == impl


def test_canonical() -> None:
    test_tableau = pauli.SignTerms.from_iterable(
        (
            (pauli.PauliMatrix.Z, pauli.PauliMatrix.Z),
            (pauli.PauliMatrix.I, pauli.PauliMatrix.Z),
        ),
        2,
    )

    test_tableau.canonicalize_all()
    assert test_tableau == pauli.SignTerms.from_iterable(
        (
            (pauli.PauliMatrix.Z, pauli.PauliMatrix.I),
            (pauli.PauliMatrix.I, pauli.PauliMatrix.Z),
        ),
        2,
    )


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


def test_compute_stabilizers_double_block() -> None:
    stabilizers = compute_stabilizers_double_block(
        identity_code(1),
        steane.logical_identity_double_block,
        2,
    )

    assert stabilizers == pauli.SignTerms.from_iterable(
        (
            (
                pauli.PauliMatrix.X,
                pauli.PauliMatrix.X,
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.I,
            ),
            (
                pauli.PauliMatrix.Z,
                pauli.PauliMatrix.Z,
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.I,
            ),
            (
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.X,
                pauli.PauliMatrix.X,
            ),
            (
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.I,
                pauli.PauliMatrix.Z,
                pauli.PauliMatrix.Z,
            ),
        ),
        4,
    )

    expanded_pauli_ops = expand_logical_signterms(stabilizers, steane.STEANE_DEF)
    assert (
        str(expanded_pauli_ops)
        == "(+1, X0 X1 X2 X3 X4 X5 X6 X7 X8 X9 X10 X11 X12 X13),"
        + " (+1, Z0 Z1 Z2 Z3 Z4 Z5 Z6 Z7 Z8 Z9 Z10 Z11 Z12 Z13),"
        + " (+1, X14 X15 X16 X17 X18 X19 X20 X21 X22 X23 X24 X25 X26 X27),"
        + " (+1, Z14 Z15 Z16 Z17 Z18 Z19 Z20 Z21 Z22 Z23 Z24 Z25 Z26 Z27)"
    )


def test_stabilizer_padding_double_block() -> None:
    padded_double_block_stabilizers = pad_code_stabilizers(
        steane.STEANE_DEF, num_blocks=2
    )
    assert len(padded_double_block_stabilizers) == 4 * (
        steane.STEANE_DEF.num_physical_qubits - steane.STEANE_DEF.num_logical_qubits
    )

    assert (
        np.all(
            padded_double_block_stabilizers.to_strings()
            .into(pauli.Strings)
            .compatibility_matrix()
        )
        == 1
    )
    assert (
        str(padded_double_block_stabilizers)
        == "X0 X1 X2 X3, X1 X2 X4 X5, X2 X3 X5 X6, Z0 Z1 Z2 Z3, Z1 Z2 Z4 Z5, Z2 Z3 Z5 Z6,"  # noqa: E501
        + " X7 X8 X9 X10, X8 X9 X11 X12, X9 X10 X12 X13, Z7 Z8 Z9 Z10, Z8 Z9 Z11 Z12, Z9 Z10 Z12 Z13,"  # noqa: E501
        + " X14 X15 X16 X17, X15 X16 X18 X19, X16 X17 X19 X20, Z14 Z15 Z16 Z17, Z15 Z16 Z18 Z19, Z16 Z17 Z19 Z20,"  # noqa: E501
        + " X21 X22 X23 X24, X22 X23 X25 X26, X23 X24 X26 X27, Z21 Z22 Z23 Z24, Z22 Z23 Z25 Z26, Z23 Z24 Z26 Z27"  # noqa: E501
    )


def test_bit_flip_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.logical_identity_double_block,
        bitflip.physical_identity_double_block,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_steane_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.logical_identity_double_block,
        steane.physical_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


def test_steane_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        steane.logical_cx,
        steane.physical_cx,
        code_definition=steane.STEANE_DEF,
    )
    assert sem == impl


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
