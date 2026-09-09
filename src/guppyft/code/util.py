"""Shared utilities, operations and types for use when defining QEC architectures."""

from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, owned
from guppylang.std.quantum import Measurement, discard_array, qubit

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


@guppy.struct
class LogicalBlock(Generic[N]):  # type: ignore[misc]
    """A logical block of ``N`` physical qubits."""

    data_qs: array[qubit, N]  # type: ignore[valid-type]

    @guppy
    @no_type_check
    def discard(self: "LogicalBlock[N]" @ owned) -> None:
        """Discard the logical block and all qubits in ``data_qs``."""
        discard_array(self.data_qs)

    @guppy
    @no_type_check
    def __getitem__(self, idx: int) -> qubit:
        return self.data_qs.take(idx)

    @guppy
    @no_type_check
    def __setitem__(self, idx: int, value: qubit @ owned) -> None:
        self.data_qs.put(value, idx)


@guppy
@no_type_check
def qalloc_dirty() -> LogicalBlock[N]:
    """Allocate resources for a codeblock, but the qubits are not in a valid logical
    state."""
    return LogicalBlock(
        array(qubit() for _ in range(N)),
    )


@guppy.struct(frozen=True)
class RawMeasurement(Generic[N]):  # type: ignore[misc]
    """An immutable Guppy struct of ``N`` measurement outcomes of the
    physical qubits in a logical block."""

    measurements: array[Measurement, N]  # type: ignore[valid-type]
