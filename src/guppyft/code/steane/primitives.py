"""Steane architecture based on https://arxiv.org/abs/2107.07505"""

from typing import no_type_check

from guppylang import guppy
from guppylang.library import link_name
from guppylang.std import quantum as qlib
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.mem import mem_swap

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
def knill_qec_cycle(
    q: LogicalBlock[7],
    a0: LogicalBlock[7] @ owned,
    a1: LogicalBlock[7] @ owned,
) -> None:
    """Implements Knill style syndrome extraction.

    Notes:
        Assumes that both ancilla blocks `a0` and `a1` hold logical
        zero states.
    """
    # Generate a logical Bell state on the ancilla qubits
    h(a0)
    cx(a0, a1)

    # Swap the labels of `q` and `a1` since the latter is where the information
    # of `q` will end after teleportation
    mem_swap(q, a1)

    # Apply Bell measurement to complete the teleportation
    cx(a1, a0)
    h(a1)
    if decode(measure_z(a0)):
        x(q)
    if decode(measure_z(a1)):
        z(q)


@guppy
@no_type_check
def steane_z_qec_cycle(q: LogicalBlock[7], a: LogicalBlock[7] @ owned) -> None:
    """Implements Z syndrome extraction via Steane with one-qubit teleportation.

    Notes:
        Assumes that the ancilla block `a` holds a logical zero state.
    """
    # Convert to logical |+>
    h(a)

    # Swap the labels of `q` and `a` since the latter is where the information
    # of `q` will end after teleportation
    mem_swap(q, a)

    # Apply one-qubit TP with physical measurements
    cx(q, a)
    if decode(measure_z(a)):
        x(q)


@guppy
@no_type_check
def steane_x_qec_cycle(q: LogicalBlock[7], a: LogicalBlock[7] @ owned) -> None:
    """Implements X syndrome extraction via Steane with one-qubit teleportation.

    Notes:
        Assumes that the ancilla block `a` holds a logical zero state.
    """
    # Swap the labels of `q` and `a` since the latter is where the information
    # of `q` will end after teleportation
    mem_swap(q, a)

    # Apply one-qubit TP with physical measurements
    cx(a, q)
    h(a)
    if decode(measure_z(a)):
        z(q)


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
    meas = qlib.collect_measurements(m.measurements)
    synds = get_syndrome(meas)
    logical_meas = parity_check(meas)
    logical_meas ^= synds[0] or synds[1] or synds[2]

    return logical_meas


@guppy
@no_type_check
def x(blk: LogicalBlock[7]) -> None:
    """Logical X gate on a Steane block."""
    for i in range(7):
        qlib.x(blk.data_qs[i])


@guppy
@no_type_check
def y(blk: LogicalBlock[7]) -> None:
    """Logical Y gate on a Steane block."""
    # Note:
    # This actually implements a logical -Y gate but as it is a global phase
    # it does not matter here.
    for i in range(7):
        qlib.y(blk.data_qs[i])


@guppy
@no_type_check
def z(blk: LogicalBlock[7]) -> None:
    """Logical Z gate on a Steane block."""
    for i in range(7):
        qlib.z(blk.data_qs[i])


@guppy
@no_type_check
def h(blk: LogicalBlock[7]) -> None:
    """Logical H gate on a Steane block."""
    for i in range(7):
        qlib.h(blk.data_qs[i])


@guppy
@no_type_check
def s(blk: LogicalBlock[7]) -> None:
    """Logical S gate on a Steane block."""
    for i in range(7):
        qlib.sdg(blk.data_qs[i])


@guppy
@no_type_check
def sdg(blk: LogicalBlock[7]) -> None:
    """Logical S dagger gate on a Steane block."""
    for i in range(7):
        qlib.s(blk.data_qs[i])


@guppy
@no_type_check
def cx(ctl: LogicalBlock[7], tgt: LogicalBlock[7]) -> None:
    """Logical CX gate between two Steane blocks."""
    for i in range(7):
        qlib.cx(ctl.data_qs[i], tgt.data_qs[i])
