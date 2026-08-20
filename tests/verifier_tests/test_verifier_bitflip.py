from guppyft.verifier.verify import (
    check_clifford_semantics,
    check_stabilizer_state_semantics,
)

from .ops import bitflip


def test_bit_flip_single_block_identity() -> None:
    assert check_clifford_semantics(
        bitflip.specify_identity,
        bitflip.implement_identity,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_double_block_identity() -> None:
    assert check_clifford_semantics(
        bitflip.specify_identity_double_block,
        bitflip.implement_identity_double_block,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_zero_state() -> None:
    assert check_stabilizer_state_semantics(
        bitflip.specify_zero_state,
        bitflip.implement_non_ft_zero_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_plus_state() -> None:
    assert check_stabilizer_state_semantics(
        bitflip.specify_plus_state,
        bitflip.implement_non_ft_plus_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_zero_state_not_plus_state() -> None:
    assert not check_stabilizer_state_semantics(
        bitflip.specify_zero_state,
        bitflip.implement_non_ft_plus_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_bell_state() -> None:
    assert check_stabilizer_state_semantics(
        bitflip.specify_bell_state,
        bitflip.implement_non_ft_bell_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_x() -> None:
    assert check_clifford_semantics(
        bitflip.specify_x,
        bitflip.implement_x,
        code_definition=bitflip.BIT_FLIP_DEF,
    )


def test_bit_flip_cx() -> None:
    assert check_clifford_semantics(
        bitflip.specify_cx,
        bitflip.implement_cx,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
