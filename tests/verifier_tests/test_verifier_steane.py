from guppyft.verifier.verify import (
    valid_clifford_implementation,
    valid_stabilizer_state_preparation,
)

from .ops import steane


def test_steane_single_block_identity() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity,
        steane.implement_identity,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_single_block_identity_with_shor_extraction() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity,
        steane.implement_identity_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        impl_num_ancillas=1,
    )


def test_steane_double_block_identity_with_shor_extraction() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block_with_shor_extraction,
        code_definition=steane.STEANE_DEF,
        impl_num_ancillas=2,
    )


def test_steane_double_block_identity() -> None:
    assert valid_clifford_implementation(
        steane.specify_identity_double_block,
        steane.implement_identity_double_block,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_zero_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_ft_zero_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_ft_zero_state,
        code_definition=steane.STEANE_DEF,
        impl_num_ancillas=7,
    )


def test_steane_plus_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_plus_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_zero_state_not_plus_state() -> None:
    assert not valid_stabilizer_state_preparation(
        steane.specify_zero_state,
        steane.implement_non_ft_plus_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_bell_state() -> None:
    assert valid_stabilizer_state_preparation(
        steane.specify_bell_state,
        steane.implement_non_ft_bell_state,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h() -> None:
    assert valid_clifford_implementation(
        steane.specify_h,
        steane.implement_h,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_h_with_ancilla() -> None:
    assert valid_clifford_implementation(
        steane.specify_h,
        steane.implement_h_with_ancilla,
        code_definition=steane.STEANE_DEF,
        impl_num_ancillas=1,
    )


def test_steane_s() -> None:
    assert valid_clifford_implementation(
        steane.specify_s,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_sdg() -> None:
    assert valid_clifford_implementation(
        steane.specify_sdg,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_invalid_s() -> None:
    assert not valid_clifford_implementation(
        steane.specify_s,
        steane.implement_sdg,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_invalid_sdg() -> None:
    assert not valid_clifford_implementation(
        steane.specify_sdg,
        steane.implement_s,
        code_definition=steane.STEANE_DEF,
    )


def test_steane_cx() -> None:
    assert valid_clifford_implementation(
        steane.specify_cx,
        steane.implement_cx,
        code_definition=steane.STEANE_DEF,
    )
