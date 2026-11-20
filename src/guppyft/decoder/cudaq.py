"""CUDA-Q QEC Realtime Decoding API in Guppy.

An implementation of the C++ API at:
https://github.com/NVIDIA/cudaqx/blob/7eae5b2/libs/qec/include/cudaq/qec/realtime/decoding.h

This module provides a Guppy interface for GPU-accelerated realtime decoding.
It includes:

- A `CudaQDecoder` class that wraps GPU-accelerated decoding functionality for
  processing syndromes and retrieving corrections in bit-packed integer format.
- Utility functions for packing and unpacking boolean arrays to/from integers for
  efficient data transfer to GPU decoders.

The module uses the `gpu` and `gpu_module` decorators available from guppy-gpu package
to enable GPU execution of quantum error correction algorithms. All syndrome and
correction data is represented as bit-packed uint64 integers with a maximum size of 64
bits.
"""

from hashlib import md5

from guppylang import guppy
from guppylang.std.builtins import array, nat
from guppylang.std.platform import panic
from guppylang_internals.decorator.gpu import gpu, gpu_module

from guppyft._math import bitstring_to_int, get_bit


def _function_id(name: bytes) -> int:
    """Return the CUDA-Q function ID from the first four MD5 bytes."""
    return int.from_bytes(md5(name, usedforsecurity=False).digest()[:4], "little")


@gpu_module("cudaq-qec", None)
class CudaQDecoder:
    """Realtime decoding using Nvidia GPUs on Quantinuum hardware.

    Corresponds to the CUDA-Q QEC Realtime decoding API at
    https://github.com/NVIDIA/cudaqx/blob/7eae5b2/libs/qec/lib/realtime/quantinuum/quantinuum_decoding.h

    The decoder maintains internal state for multiple decoder instances, each identified
    by a unique `decoder_id`. Syndromes are enqueued for processing, and corrections
    (detected bit flips) can be retrieved after decoding.

    Note:
        All syndrome and correction data is represented as bit-packed integers (uint64),
        with a maximum size of 64 bits per operation.
    """

    @gpu(_function_id(b"enqueue_syndromes_ui64"))
    def enqueue_syndromes(
        self, decoder_id: int, syndrome_size: int, syndrome: int, tag: int
    ) -> None:
        """Enqueue a syndrome for decoding.

        Args:
            decoder_id (int): The ID of the decoder to use.
            syndrome_size (int): The size of the syndrome (in bits). This must be <= 64.
            syndrome (int): The bit-packed syndrome to enqueue. The least significant
                            bit (i.e. syndrome & 1) is the first bit of the syndrome.
                            The last valid bit is `syndrome_size - 1`
                            (i.e. syndrome & (1 << (syndrome_size - 1)).
            tag (int): The tag to use for the syndrome (logging only).
        """

    @gpu(_function_id(b"get_corrections_ui64"))
    def get_corrections(self, decoder_id: int, return_size: int, reset: int) -> int:  # type: ignore[empty-body]
        """Get the corrections for a given decoder.

        Args:
            decoder_id (int): The ID of the decoder to use.
            return_size (int): The number of bits to return (in bits). This must be
                               <= 64. This is expected to match the number of
                               observables in the decoder. The least significant bit
                               (i.e. return_value & 1) is the first bit of the
                               corrections. The last valid bit is `return_size - 1`.
            reset (int): Whether to reset the decoder corrections after retrieving them.

        Returns:
            int: The corrections (detected bit flips) for the given decoder, based on
                 all of the decoded syndromes since the last time any corrections were
                 reset.
        """

    @gpu(_function_id(b"reset_decoder_ui64"))
    def reset_decoder(self, decoder_id: int) -> None:
        """Reset the decoder. This clears any queued syndromes and resets any
        corrections back to 0.

        Args:
            decoder_id (int): The ID of the decoder to reset.
        """


# TODO: Replace these helpers with `array.to_nat()` and `array_from_nat` when
# released in Guppy. See https://github.com/Quantinuum/guppylang/pull/2485.
@guppy
def pack_int[N: nat](data: array[bool, N]) -> int:
    """Pack at most 64 bits, most significant bit first."""
    if len(data) > 64:
        panic("CUDA-Q decoder bit arrays cannot exceed 64 bits")
    return bitstring_to_int(data)  # type: ignore[no-any-return]


@guppy
def unpack_int[N: nat](data: int) -> array[bool, N]:
    """Unpack the lowest `N` bits, most significant bit first."""
    return array(get_bit(data, N - n - 1) for n in range(N))  # type: ignore[misc, no-any-return]
