from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.array import ArrayIter
from guppylang.std.builtins import array, owned
from guppylang.std.iter import SizedIter
from guppylang.std.quantum import Measurement, discard, qubit

N = guppy.nat_var("N")


@guppy
@no_type_check
def parity_check(data_bits: array[bool, N]) -> bool:
    """Compute the XOR (parity) of all bits in ``data_bits``."""
    out = False
    for i in range(N):
        out ^= data_bits[i]
    return out


@guppy.struct
class LogicalBlock(Generic[N]):  # type: ignore[misc]
    """A logical block of ``N`` physical qubits."""

    data_qs: array[qubit, N]  # type: ignore[valid-type]

    @guppy
    @no_type_check
    def discard(self: "LogicalBlock[N]" @ owned) -> None:
        """Discard the logical block and all qubits in ``data_qs``."""
        for q in self.data_qs:
            discard(q)

    @guppy
    @no_type_check
    def __iter__(self: "LogicalBlock[N]" @ owned) -> SizedIter[ArrayIter[qubit, N], N]:
        return array(q for q in self.data_qs).__iter__()


@guppy.struct(frozen=True)
class RawMeasurement(Generic[N]):  # type: ignore[misc]
    """An immutable Guppy struct of ``N`` measurement outcomes of the
    physical qubits in a logical block."""

    measurements: array[Measurement, N]  # type: ignore[valid-type]
