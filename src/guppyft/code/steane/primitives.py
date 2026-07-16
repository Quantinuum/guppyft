"""Steane architecture based on https://arxiv.org/abs/2107.07505"""

from typing import no_type_check

from guppylang import guppy
from guppylang.library import link_name
from guppylang.std import quantum as qlib
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.quantum import collect_measurements

from guppyft.code.util import LogicalBlock, LogicalMeasurement, parity_check

# ZZZZIII -> 0, 1, 2, 3
# IZZIZZI -> 1, 2, 4, 5
# IIZZIZZ -> 2, 3, 5, 6
stabilizer_indices = [
    [0, 1, 2, 3],
    [1, 2, 4, 5],
    [2, 3, 5, 6],
]


@guppy
@link_name("guppyft.Steane.prep_zero")
@no_type_check
def prep_zero() -> LogicalBlock[7]:
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
def get_syndrome(data_bits: array[bool, 7]) -> array[bool, 3]:
    return array(
        parity_check(array(data_bits[i] for i in stab))
        for stab in comptime(stabilizer_indices)
    )


@guppy
@link_name("guppyft.Steane.measure_z")
@no_type_check
def measure_z(blk: LogicalBlock[7] @ owned) -> LogicalMeasurement[7]:
    """Measure Steane block in the Z basis."""
    return LogicalMeasurement(qlib.measure_array(blk.data_qs))


@guppy
@link_name("guppyft.Steane.decode")
@no_type_check
def decode(m: LogicalMeasurement[7] @ owned) -> array[bool, 1]:
    """Decode Steane measurement of logical block"""
    meas = collect_measurements(m.measurements)
    synds = get_syndrome(meas)
    logical_meas = parity_check(meas)
    logical_meas ^= synds[0] or synds[1] or synds[2]

    return array(logical_meas)
