from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
    compute_verification_signterms_double_block_state,
    compute_verification_signterms_single_block_state,
)

from .ops import bitflip


def test_bit_flip_single_block_identity() -> None:
    sem, impl = compute_verification_signterms(
        bitflip.specify_identity,
        bitflip.implement_identity,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.specify_identity_double_block,
        bitflip.implement_identity_double_block,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_zero_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        bitflip.specify_zero_state,
        bitflip.implement_non_ft_zero_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        bitflip.specify_plus_state,
        bitflip.implement_non_ft_plus_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_zero_state_not_plus_state() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        bitflip.specify_zero_state,
        bitflip.implement_non_ft_plus_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem != impl


def test_bit_flip_bell_state() -> None:
    sem, impl = compute_verification_signterms_double_block_state(
        bitflip.specify_bell_state,
        bitflip.implement_non_ft_bell_state,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_x() -> None:
    sem, impl = compute_verification_signterms(
        bitflip.specify_x,
        bitflip.implement_x,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.specify_cx,
        bitflip.implement_cx,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl
