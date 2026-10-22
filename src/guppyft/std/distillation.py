"""Magic state distillation built from a code's own logical operations."""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.lang import Drop, Function
from guppylang.std.option import Option, nothing, some

from .state_factory import PreBlock

__all__ = [
    "Distillation15To1",
    "Distillation15To1Ops",
    "Distillation15To1QECPolicy",
    "DistillationFlags",
]

_N_BLOCKS = 16
_N_OUTCOMES = _N_BLOCKS - 1
_PLUS_IDXS = [0, 1, 2, 4, 8]

# CX layers encoding the first-order Reed-Muller state on 16 blocks.
# fmt: off
_ENCODER_CX_PAIRS = [
    (1, 9), (2, 10), (4, 12),
    (0, 4), (1, 5), (2, 6),
    (8, 12), (9, 13), (10, 14),
    (0, 2), (1, 3),
    (4, 6), (5, 7),
    (8, 10), (9, 11),
    (12, 14), (13, 15),
    (0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15),
]
# fmt: on

# Blocks whose X outcomes form each X stabilizer of the 15-qubit code.
# https://errorcorrectionzoo.org/c/stab_15_1_3
_X_CHECK_SUPPORTS = [
    [1, 3, 5, 7, 9, 11, 13, 15],
    [2, 3, 6, 7, 10, 11, 14, 15],
    [4, 5, 6, 7, 12, 13, 14, 15],
    [8, 9, 10, 11, 12, 13, 14, 15],
]


@guppy
@no_type_check
def _checks_pass(bits: array[bool, comptime(_N_OUTCOMES)]) -> bool:
    for support in comptime(_X_CHECK_SUPPORTS):
        parity = False
        for j in support:
            # Block 0 is not measured, so block `j` is at index `j - 1`.
            parity ^= bits[j - 1]
        if parity:
            return False
    return True


@guppy
@no_type_check
def _parity(bits: array[bool, comptime(_N_OUTCOMES)]) -> bool:
    parity = False
    for i in range(comptime(_N_OUTCOMES)):
        parity ^= bits[i]
    return parity


@guppy.struct(frozen=True)
class Distillation15To1Ops[Q, M]:  # type: ignore[misc]
    r"""Logical operations a code must provide for `Distillation15To1`.

    Type parameters:
        Q: The code's logical qubit type.
        M: The code's logical measurement type, decoded with `decode`.

    Attributes:
        prep_noisy_t: Prepare a qubit in the logical :math:`T\ket{+}` state, not
            necessarily fault-tolerantly.
        h: Apply a logical H gate.
        sdg: Apply a logical S dagger gate.
        z: Apply a logical Z gate.
        cx: Apply a logical CX gate, given the control then the target.
        measure_z: Measure the qubit in the logical Z basis, without decoding.
        decode: Decode a logical measurement outcome.
    """

    prep_noisy_t: Function[[], Q]  # type: ignore[type-arg,valid-type]
    h: Function[[Q], None]  # type: ignore[type-arg,valid-type,misc]
    sdg: Function[[Q], None]  # type: ignore[type-arg,valid-type,misc]
    z: Function[[Q], None]  # type: ignore[type-arg,valid-type,misc]
    cx: Function[[Q, Q], None]  # type: ignore[type-arg,valid-type]
    measure_z: Function[[Q @ owned], M]  # type: ignore[type-arg,valid-type,misc]
    decode: Function[[M @ owned], bool]  # type: ignore[type-arg,valid-type,misc]


@guppy.struct(frozen=True)
class Distillation15To1QECPolicy:  # type: ignore[misc]
    """When `Distillation15To1.prepare` applies QEC cycles to its qubits.

    Each qubit accumulates the cost of the operations applied to it, and gets a QEC
    cycle once its total reaches `threshold`, which resets the total.

    Attributes:
        threshold: Accumulated cost at which a qubit gets a QEC cycle.
        prep_zero: Cost of each qubit's initial zero state.
        h: Cost of a logical H gate.
        cx: Cost of a logical CX gate, charged to both qubits.
        inject_tdg: Cost of injecting T dagger into a qubit.
    """

    threshold: float
    prep_zero: float
    h: float
    cx: float
    inject_tdg: float


@guppy
@no_type_check
def _charge[Q, R](
    qs: array[Q, comptime(_N_BLOCKS)],
    counters: array[float, comptime(_N_BLOCKS)],
    i: int,
    cost: float,
    policy: Distillation15To1QECPolicy,
    resources: R,
    qec: Function[[R, Q], None],
) -> None:
    counters[i] = counters[i] + cost
    if counters[i] >= policy.threshold:
        qec(resources, qs[i])
        counters[i] = 0.0


@guppy
@no_type_check
def _inject_tdg[Q, M: Drop](
    ops: Distillation15To1Ops[Q, M],
    q: Q,
    t_state: Q @ owned,
) -> None:
    r"""Apply T dagger to `q` by consuming a :math:`T\ket{+}` state."""
    ops.cx(q, t_state)
    m = ops.measure_z(t_state)
    if not ops.decode(m):
        ops.sdg(q)


@guppy.struct
class DistillationFlags[Q, M]:
    """Unread X-basis outcomes of a 15-to-1 distillation round.

    Attributes:
        ops: The code's operations, used to decode the outcomes and correct the output.
        outcomes: Measurement outcomes of blocks 1 to 15.
    """

    ops: Distillation15To1Ops[Q, M]
    outcomes: array[M, comptime(_N_OUTCOMES)]  # type: ignore[valid-type]


@guppy
@no_type_check
def _distillation_check[Q, M: Drop](
    q: Q @ owned, flags: DistillationFlags[Q, M] @ owned
) -> Option[Q]:
    """Check if the distilled state passes the X stabilizer checks.
    If the checks pass, returns `some(q)` with the corrected state.
    """
    ops = flags.ops
    bits = array(ops.decode(m) for m in flags.outcomes)
    if not _checks_pass(bits):
        # Measuring discards `q`
        ops.measure_z(q)
        return nothing()
    if _parity(bits):
        ops.z(q)
    return some(q)


@guppy
@no_type_check
def _distillation_discard[Q, M: Drop](
    q: Q @ owned, flags: DistillationFlags[Q, M] @ owned
) -> None:
    flags.ops.measure_z(q)


@guppy.struct
class Distillation15To1[Q, M: Drop]:
    r"""15-to-1 :math:`T\ket{+}` distillation using the [[15, 1, 3]] Reed-Muller code.

    Qubit 0 is entangled with a 15-qubit Reed-Muller code block, on which transversal
    T dagger (via noisy :math:`T\ket{+}` injection) acts as a logical T. Measuring the
    15 qubits in the X basis teleports :math:`T\ket{+}` onto qubit 0, and the X
    stabilizer parities detect faulty injections.

    Circuit taken from Fig. 8 of:
    https://journals.aps.org/prxquantum/pdf/10.1103/PRXQuantum.2.020341

    Attributes:
        ops: The code's operations used to implement the circuit.
    """

    ops: Distillation15To1Ops[Q, M]

    @guppy
    @no_type_check
    def prepare[R](
        self,
        resources: R,
        prep_zero: Function[[R], Q],
        qec: Function[[R, Q], None],
        qec_policy: Distillation15To1QECPolicy,
    ) -> PreBlock[Q, DistillationFlags[Q, M]]:
        r"""Run one distillation round without reading the X-basis outcomes.

        Calling `force_check` on the result reads the outcomes, and returns the
        distilled :math:`T\ket{+}` state, or `nothing` if a check failed.

        Args:
            resources: Resources passed to `prep_zero` and `qec`, e.g. a factory of
                zero states.
            prep_zero: Prepares a qubit in the logical zero state.
            qec: Applies a QEC cycle to a qubit.
            qec_policy: When to apply `qec` to each of the 16 qubits.
        """
        qs = array(prep_zero(resources) for _ in range(comptime(_N_BLOCKS)))
        counters = array(0.0 for _ in range(comptime(_N_BLOCKS)))
        for i in range(comptime(_N_BLOCKS)):
            _charge(qs, counters, i, qec_policy.prep_zero, qec_policy, resources, qec)

        for i in comptime(_PLUS_IDXS):
            self.ops.h(qs[i])
            _charge(qs, counters, i, qec_policy.h, qec_policy, resources, qec)
        for c, t in comptime(_ENCODER_CX_PAIRS):
            self.ops.cx(qs[c], qs[t])
            _charge(qs, counters, c, qec_policy.cx, qec_policy, resources, qec)
            _charge(qs, counters, t, qec_policy.cx, qec_policy, resources, qec)

        for j in range(1, comptime(_N_BLOCKS)):
            t_state = self.ops.prep_noisy_t()
            _inject_tdg(self.ops, qs[j], t_state)
            _charge(qs, counters, j, qec_policy.inject_tdg, qec_policy, resources, qec)
            self.ops.h(qs[j])
            _charge(qs, counters, j, qec_policy.h, qec_policy, resources, qec)

        outcomes = array(
            self.ops.measure_z(qs.take(i + 1)) for i in range(comptime(_N_OUTCOMES))
        )
        out = qs.take(0)
        qs.discard_all_taken()

        return PreBlock(
            out,
            DistillationFlags(self.ops, outcomes),
            _distillation_check,
            _distillation_discard,
        )
