from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.lang import owned
from guppylang.std.quantum import discard_array, qubit

BLOCK_SIZE = guppy.nat_var("BLOCK_SIZE")


@guppy.struct
class LogicalBlock(Generic[BLOCK_SIZE]):  # type: ignore[misc]
    """A logical block of ``N`` physical qubits."""

    data_qs: array[qubit, BLOCK_SIZE]  # type: ignore[valid-type]

    @guppy
    @no_type_check
    def discard(self: "LogicalBlock[BLOCK_SIZE]" @ owned) -> None:
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
