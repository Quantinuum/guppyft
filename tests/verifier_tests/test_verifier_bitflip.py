from guppyft.verifier.verify import compute_verification_signterms_double_block

from .ops import bitflip


def test_bit_flip_double_block_identity() -> None:
    sem, impl = compute_verification_signterms_double_block(
        bitflip.logical_identity_double_block,
        bitflip.physical_identity_double_block,
        code_definition=bitflip.BIT_FLIP_DEF,
    )
    assert sem == impl
