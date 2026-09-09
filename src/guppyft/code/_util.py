"""Shared utilities, operations and types for use when defining QEC architectures."""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array

N = guppy.nat_var("N")


@guppy
@no_type_check
def parity_check(data_bits: array[bool, N]) -> bool:
    """Compute the XOR (parity) of all bits in ``data_bits``."""
    out = False
    for i in range(N):
        out ^= data_bits[i]
    return out


@guppy
@no_type_check
def array_any(arr: array[bool, N]) -> bool:
    for i in range(N):  # noqa: SIM110 # `all` is not yet supported by Guppy
        if arr[i]:
            return True
    return False
