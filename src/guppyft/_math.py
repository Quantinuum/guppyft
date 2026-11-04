"""Guppy runtime math functions.

Duplicated from guppy-algos to avoid circular imports.
These should be added to guppylang.
    (https://github.com/Quantinuum/guppylang/issues/1204)

Original contribution: @vvandaele (Vivien Vandaele)
"""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array

N = guppy.nat_var("N")


@guppy
@no_type_check
def get_bit(k: int, i: int) -> bool:
    """Extract bit i from integer k.

    Args:
        k: Integer value.
        i: Bit position, where 0 is the rightmost (least significant) bit.

    Returns:
        bool: True if bit i is 1, False otherwise.
    """
    return ((k >> i) & 1) == 1


@guppy
@no_type_check
def bitstring_to_int(data_bits: array[bool, N]) -> int:
    """Convert bitstring to int with data_bits[0] being most significant."""
    out = 0
    for i in range(N):
        out <<= 1
        if data_bits[i]:
            out += 1
    return out


@guppy
@no_type_check
def floor(x: float) -> int:
    """Compute the largest integer less than or equal to x.

    Args:
        x: Floating-point value.

    Returns:
        int: Largest integer less than or equal to x.
    """
    i = int(x)
    if float(i) > x:
        return i - 1
    return i
