from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, owned
from guppylang.std.collections import Stack
from guppylang.std.option import Option
from guppylang.std.quantum import Measurement, discard, qubit

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

    @guppy
    @no_type_check
    def discard(self: "LogicalBlock[N]" @ owned) -> None:
        for q in self.data_qs:
            discard(q)


@guppy.struct
class LogicalMeasurement(Generic[N]):  # type: ignore[misc]
    measurements: array[Measurement, N]  # type: ignore[valid-type]


@guppy.protocol
class GlobalState:
    blocks: array[Option[LogicalBlock[7]], 1]  # type: ignore[type-arg, valid-type]
    addr_stack: Stack[tuple[int, int], 1]  # type: ignore[type-arg, valid-type]

    @guppy.declare
    def allocate_blk_addr(self) -> tuple[int, int]:  # type: ignore[empty-body]
        pass

    @guppy.declare
    def free_blk_addr(self, addr: tuple[int, int]) -> None:
        pass
