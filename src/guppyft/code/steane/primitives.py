"""Implementations of primitives for the Steane QEC architecture.

Primitives should be restricted to the most fundamental building blocks of a
QEC architecture. Operations that comprise multiple primitives should be added to
:py:mod:`~guppyft.code.steane.logical` instead.

Based on https://arxiv.org/abs/2107.07505"""

from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.library import link_name
from guppylang.std import quantum as qlib
from guppylang.std.angles import pi
from guppylang.std.builtins import Measurement, array, comptime, owned
from guppylang.std.mem import mem_swap
from zixy.qubit import pauli

from guppyft.code_def import StabilizerCode
from guppyft.std import LogicalBlock
from guppyft.std.state_factory import PreBlock

__all__ = [
    "CODE_DEF",
    "RawMeasurement",
    "cx",
    "cz",
    "decode",
    "h",
    "inject_t",
    "inject_tdg",
    "knill_qec_cycle",
    "measure_z",
    "prep_t_state_ft",
    "prep_zero_ft",
    "prep_zero_non_ft",
    "s",
    "sdg",
    "steane_x_qec_cycle",
    "steane_z_qec_cycle",
    "x",
    "y",
    "z",
]

CODE_DEF = StabilizerCode.from_python_strings(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
    x_logicals=["XXXXXXX"],
    z_logicals=["ZZZZZZZ"],
)


def _stabilizer_indices() -> list[list[int]]:
    """Report all support sets that exist in the Steane codes generators. Values are
    unique but reported as a nested list so that Guppy can understand them."""

    indices = {
        frozenset([i for i, p in enumerate(gen.cmpnt.get_tuple()) if p != pauli.I])  # type: ignore[attr-defined]
        for gen in CODE_DEF.generators
    }

    return [list(idxs) for idxs in indices]


N = guppy.nat_var("N")


@guppy
@no_type_check
def _parity_check(data_bits: array[bool, N]) -> bool:
    """Compute the XOR (parity) of all bits in ``data_bits``."""
    out = False
    for i in range(N):
        out ^= data_bits[i]
    return out


@guppy
@no_type_check
def prep_zero_non_ft() -> LogicalBlock[7]:
    """Prepare Steane block in the logical zero state."""
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


@guppy.comptime
@no_type_check
def _syndrome_helper(
    a: array[qlib.qubit, 3],
    blk: LogicalBlock[7],
    idx: tuple[int, int, int] @ comptime,
    reverse_cx: bool @ comptime,
) -> None:
    """Helper function to perform the cx operations during syndrome extraction."""

    if reverse_cx:
        qlib.cx(blk.data_qs[idx[0]], a[0])
        qlib.cx(a[1], blk.data_qs[idx[1]])
        qlib.cx(a[2], blk.data_qs[idx[2]])
    else:
        qlib.cx(a[0], blk.data_qs[idx[0]])
        qlib.cx(blk.data_qs[idx[1]], a[1])
        qlib.cx(blk.data_qs[idx[2]], a[2])


@guppy.comptime
@no_type_check
def _measure_syndromes(blk: LogicalBlock[7]) -> array[qlib.Measurement, 6]:
    """Syndrome measurement using Figure 5. from Reichardt arXiv:1804.06995."""

    relabel = array(0, 4, 1, 6, 3, 5, 2)

    # Prepare ancilla state
    a_xzz = array(qlib.qubit() for _ in range(3))
    qlib.h(a_xzz[0])

    _syndrome_helper(a_xzz, blk, (relabel[4], relabel[6], relabel[5]), False)
    qlib.cx(a_xzz[0], a_xzz[2])
    _syndrome_helper(a_xzz, blk, (relabel[0], relabel[4], relabel[1]), False)
    _syndrome_helper(a_xzz, blk, (relabel[2], relabel[3], relabel[6]), False)
    qlib.cx(a_xzz[0], a_xzz[1])
    _syndrome_helper(a_xzz, blk, (relabel[6], relabel[5], relabel[2]), False)

    qlib.h(a_xzz[0])
    m_xzz = qlib.measure_array(a_xzz)

    # Prepare ancilla state
    a_zxx = array(qlib.qubit() for _ in range(3))
    qlib.h(a_zxx[1])
    qlib.h(a_zxx[2])

    _syndrome_helper(a_zxx, blk, (relabel[4], relabel[6], relabel[5]), True)
    qlib.cx(a_zxx[2], a_zxx[0])
    _syndrome_helper(a_zxx, blk, (relabel[0], relabel[4], relabel[1]), True)
    _syndrome_helper(a_zxx, blk, (relabel[2], relabel[3], relabel[6]), True)
    qlib.cx(a_zxx[1], a_zxx[0])
    _syndrome_helper(a_zxx, blk, (relabel[6], relabel[5], relabel[2]), True)

    qlib.h(a_zxx[1])
    qlib.h(a_zxx[2])
    m_zxx = qlib.measure_array(a_zxx)

    return array(m_xzz[0], m_xzz[1], m_xzz[2], m_zxx[0], m_zxx[1], m_zxx[2])


@guppy
def _phys_controlled_h(ctl: qlib.qubit, tgt: qlib.qubit) -> None:
    """Implements controlled-H gate between physical qubits."""
    qlib.ry(tgt, -pi / 4)
    qlib.cz(ctl, tgt)
    qlib.ry(tgt, pi / 4)


@guppy
@no_type_check
def _measure_h_operator(blk: LogicalBlock[7]) -> array[qlib.Measurement, 2]:
    """Fault-tolerant measurement of the logical H operator on a Steane block."""
    # Prepare Bell state ancilla
    a = array(qlib.qubit() for _ in range(2))
    qlib.h(a[0])
    qlib.cx(a[0], a[1])

    # Apply controlled-H gates
    for tgt in range(7):
        _phys_controlled_h(
            a[tgt % 2],  # Alternate control qubit for parallelization
            blk[tgt],
        )

    # Measure ancilla
    qlib.cx(a[0], a[1])
    qlib.h(a[0])
    return qlib.measure_array(a)


@guppy.comptime
@no_type_check
def _prep_h_non_ft() -> LogicalBlock[7]:
    """Non-fault-tolerant preparation of an |H> = Ry(pi/4)|0> magic state on
    a Steane block.

    Using Fig. 3b from "Minimizing resource overheads for fault-tolerant
    preparation of encoded states of the Steane code" 10.1038/srep19578.

    To match with our definition of the code stabilizers, we relabel qubits
    from Fig 3b from top to bottom as: [1, 0, 4, 5, 2, 6, 3]
    """

    relabel = array(1, 0, 4, 5, 2, 6, 3)

    arr = array(qlib.qubit() for _ in range(7))
    # Prepare qubit `1` in the |H> = Ry(pi/4)|0> state
    qlib.ry(arr[relabel[0]], pi / 4)
    # Prepare qubits that start in |+> state.
    qlib.h(arr[relabel[1]])
    qlib.h(arr[relabel[2]])
    qlib.h(arr[relabel[5]])
    # Apply the CNOTs
    cx_pairs = array(
        (0, 6),
        (0, 3),
        (1, 0),
        (5, 4),
        (2, 3),
        (1, 6),
        (2, 4),
        (5, 3),
        (1, 4),
        (2, 0),
        (5, 6),
    )
    for ctl, tgt in cx_pairs:
        qlib.cx(arr[relabel[ctl]], arr[relabel[tgt]])

    return LogicalBlock(arr)


@guppy.comptime
@no_type_check
def _prep_h_ft() -> PreBlock[7, 8]:
    """Fault-tolerant preparation of an |H> = Ry(pi/4)|0> magic state on
    a Steane block.

    Using Fig. 3b from "Minimizing resource overheads for fault-tolerant
    preparation of encoded states of the Steane code" 10.1038/srep19578.
    """

    blk = _prep_h_non_ft()
    m_h = _measure_h_operator(blk)
    m_syn = _measure_syndromes(blk)
    m = array(
        m_h[0], m_h[1], m_syn[0], m_syn[1], m_syn[2], m_syn[3], m_syn[4], m_syn[5]
    )

    return PreBlock(blk, m)


@guppy
@no_type_check
def prep_t_state_ft() -> PreBlock[7, 8]:
    """Attempt to prepare a T|+> logical state on a Steane block."""
    # Attempt |H> = Ry(pi/4)|0> state preparation
    preblock = _prep_h_ft()
    # Convert to Rz(pi/4)|+> state
    sdg(preblock.logical_block)
    h(preblock.logical_block)

    return preblock


@guppy
@no_type_check
def _inject_t_non_deterministically(
    blk: LogicalBlock[7], t_state: LogicalBlock[7] @ owned
) -> bool:
    """Inject T gate, but do not apply corrections.

    Note:
        Assumes `t_state` is a logical T|+> magic state.
    """
    a = t_state  # Rename to avoid confusion, since the state will change
    # Inject (via teleportation)
    cx(a, blk)
    # SWAP logical information, so that we can complete the TP by destructively
    # measuring the resource (which we own)
    mem_swap(a, blk)
    return decode(measure_z(a))


@guppy
@no_type_check
def inject_t(blk: LogicalBlock[7], t_state: LogicalBlock[7] @ owned) -> None:
    """Apply T gate via injection.

    Note:
        Assumes `t_state` is a logical T|+> magic state.
    """
    meas = _inject_t_non_deterministically(blk, t_state)
    if meas:
        x(blk)
        s(blk)


@guppy
@no_type_check
def inject_tdg(blk: LogicalBlock[7], t_state: LogicalBlock[7] @ owned) -> None:
    """Apply Tdg gate via injection.

    Note:
        Assumes `t_state` is a logical T|+> magic state.
    """
    meas = _inject_t_non_deterministically(blk, t_state)
    if meas:
        x(blk)
    else:
        sdg(blk)


@guppy
@no_type_check
def _get_syndrome(data_bits: array[bool, 7]) -> array[bool, 3]:
    return array(
        _parity_check(array(data_bits[i] for i in stab))
        for stab in comptime(_stabilizer_indices())
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


N = guppy.nat_var("N")


@guppy.struct(frozen=True)
class RawMeasurement(Generic[N]):  # type: ignore[misc]
    """An immutable Guppy struct of ``N`` measurement outcomes of the
    physical qubits in a logical block."""

    measurements: array[Measurement, N]  # type: ignore[valid-type]


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
    synds = _get_syndrome(meas)
    logical_meas = _parity_check(meas)
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


@guppy
@no_type_check
def cz(q0: LogicalBlock[7], q1: LogicalBlock[7]) -> None:
    """Logical CZ gate between two Steane blocks."""
    for i in range(7):
        qlib.cz(q0.data_qs[i], q1.data_qs[i])
