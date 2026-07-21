from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
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
