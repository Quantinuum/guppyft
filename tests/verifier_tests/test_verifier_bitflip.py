from guppyft.verifier.verify import (
    compute_verification_signterms,
    compute_verification_signterms_double_block,
)

from .ops import bitflip


def test_bit_flip_single_block_identity() -> None:
    sem, impl = compute_verification_signterms(
        bitflip.logical_identity,
        bitflip.physical_identity,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.logical_identity_double_block,
        bitflip.physical_identity_double_block,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_x() -> None:
    sem, impl = compute_verification_signterms(
        bitflip.logical_x,
        bitflip.physical_x,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl


def test_bit_flip_cx() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.logical_cx,
        bitflip.physical_cx,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl
