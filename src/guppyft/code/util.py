from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import Measurement, qubit

N = guppy.nat_var("N")


@guppy
@no_type_check
def parity_check(data_bits: array[bool, N]) -> bool:
    out = False
    for i in range(N):
        out ^= data_bits[i]
    return out


@guppy.struct
class LogicalBlock(Generic[N]):  # type: ignore[misc]
    data_qs: array[qubit, N]  # type: ignore[valid-type]


@guppy.struct
class LogicalMeasurement(Generic[N]):  # type: ignore[misc]
    measurements: array[Measurement, N]  # type: ignore[valid-type]
