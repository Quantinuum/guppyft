from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array

N = guppy.nat_var("N")


@guppy
@no_type_check
def parity_check(data_bits: array[bool, N]) -> bool:
    out = False
    for i in range(N):
        out ^= data_bits[i]
    return out
