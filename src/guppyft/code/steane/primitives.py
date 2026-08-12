"""Steane architecture based on https://arxiv.org/abs/2107.07505"""

from typing import no_type_check

from guppylang import guppy
from guppylang.library import link_name
from guppylang.std import quantum as qlib
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.quantum import collect_measurements

from guppyft.code._state_factory import PreBlock
from guppyft.code.util import LogicalBlock, RawMeasurement, parity_check

# ZZZZIII -> 0, 1, 2, 3
# IZZIZZI -> 1, 2, 4, 5
# IIZZIZZ -> 2, 3, 5, 6
stabilizer_indices = [
    [0, 1, 2, 3],
    [1, 2, 4, 5],
    [2, 3, 5, 6],
]


@guppy
@no_type_check
def prep_zero_non_ft() -> LogicalBlock[7]:
    """Prepare Steane blk in the logical zero state."""
    blk = LogicalBlock(array(qlib.qubit() for _ in range(7)))

    plus_ids = array(0, 4, 6)
    for i in plus_ids:
        qlib.h(blk.data_qs[i])

    cx_pairs = array((0, 1), (4, 5), (6, 3), (6, 5), (4, 2), (0, 3), (4, 1), (3, 2))
    for c, t in cx_pairs:
        qlib.cx(blk.data_qs[c], blk.data_qs[t])

    return blk


@guppy
@no_type_check
def prep_zero_ft() -> PreBlock[7, 1]:
    """Attempt fault-tolerant zero preparation state once."""
    q = prep_zero_non_ft()

    ancilla = qlib.qubit()
    idxs = array(1, 3, 5)
    for i in idxs:
        qlib.cx(q.data_qs[i], ancilla)

    flag_outcome = qlib.measure(ancilla)
    return PreBlock[7, 1](q, array(flag_outcome))


@guppy
@no_type_check
def get_syndrome(data_bits: array[bool, 7]) -> array[bool, 3]:
    return array(
        parity_check(array(data_bits[i] for i in stab))
        for stab in comptime(stabilizer_indices)
    )


@guppy
@no_type_check
def measure_z(blk: LogicalBlock[7] @ owned) -> RawMeasurement[7]:
    """Measure Steane block in the Z basis."""
    return RawMeasurement(qlib.measure_array(blk.data_qs))


@guppy
@link_name("guppyft.steane.decode")
@no_type_check
def decode(m: RawMeasurement[7] @ owned) -> bool:
    """Decode Steane measurement of logical block"""
    meas = collect_measurements(m.measurements)
    synds = get_syndrome(meas)
    logical_meas = parity_check(meas)
    logical_meas ^= synds[0] or synds[1] or synds[2]

    return logical_meas


@guppy
@no_type_check
def x(blk: LogicalBlock[7]) -> None:
    for i in range(7):
        qlib.x(blk.data_qs[i])


@guppy
@no_type_check
def z(blk: LogicalBlock[7]) -> None:
    for i in range(7):
        qlib.z(blk.data_qs[i])


@guppy
@no_type_check
def h(blk: LogicalBlock[7]) -> None:
    for i in range(7):
        qlib.h(blk.data_qs[i])


@guppy
@no_type_check
def cx(ctl: LogicalBlock[7], tgt: LogicalBlock[7]) -> None:
    for i in range(7):
        qlib.cx(ctl.data_qs[i], tgt.data_qs[i])
