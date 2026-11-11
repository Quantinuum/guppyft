"""15-to-1 magic state distillation built from a code's own logical operations."""

from typing import Self, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, comptime, exit, nat, owned, panic
from guppylang.std.collections import Queue
from guppylang.std.lang import Drop, Function
from guppylang.std.option import Option, nothing, some

__all__ = [
    "DistillationFactory",
    "DistillationOps",
    "DistillationPreBlock",
    "DistillationQECPolicy",
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


@guppy
@no_type_check
def _inject_tdg[Q, M: Drop](
    ops: "DistillationOps[Q, M]",
    q: Q,
    t_state: Q @ owned,
) -> None:
    r"""Apply T dagger to `q` by consuming a :math:`T\ket{+}` state."""
    ops.cx(q, t_state)
    m = ops.measure_z(t_state)
    if not ops.decode(m):
        ops.sdg(q)


@guppy.struct(frozen=True)
class DistillationOps[Q, M]:  # type: ignore[misc]
    r"""Logical operations a code must provide for `DistillationFactory`.

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
class DistillationQECPolicy:  # type: ignore[misc]
    """When `DistillationFactory` applies QEC cycles to the qubits of a round.

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


@guppy.struct
class DistillationPreBlock[Q, M: Drop]:
    """Output of a 15-to-1 distillation round whose X-basis outcomes are unread.

    Type parameters:
        Q: The code's logical qubit type.
        M: The code's logical measurement type.

    Attributes:
        state: The candidate distilled state.
        ops: The code's operations, used to decode the outcomes and correct the output.
        outcomes: Measurement outcomes of blocks 1 to 15.
    """

    state: Q
    ops: DistillationOps[Q, M]
    outcomes: array[M, comptime(_N_OUTCOMES)]  # type: ignore[valid-type]

    @guppy
    @no_type_check
    def force_check(self: Self @ owned) -> Option[Q]:
        """Return the corrected state if the X stabilizer checks pass, otherwise
        `nothing`."""
        bits = array(self.ops.decode(m) for m in self.outcomes)
        if not _checks_pass(bits):
            # Measuring discards the state
            self.ops.measure_z(self.state)
            return nothing()
        if _parity(bits):
            self.ops.z(self.state)
        return some(self.state)

    @guppy
    @no_type_check
    def discard(self: Self @ owned) -> None:
        """Discard the candidate state without checking it."""
        self.ops.measure_z(self.state)


@guppy.struct
class DistillationFactory[Q, M: Drop, C, BATCH_SIZE: nat]:
    r"""Factory of :math:`T\ket{+}` states made by 15-to-1 distillation, running rounds
    in parallel until one passes its checks.

    Each round uses the [[15, 1, 3]] Reed-Muller code. Qubit 0 is entangled with a
    15-qubit Reed-Muller code block, on which transversal T dagger (via noisy
    :math:`T\ket{+}` injection) acts as a logical T. Measuring the 15 qubits in the X
    basis teleports :math:`T\ket{+}` onto qubit 0, and the X stabilizer parities
    detect faulty injections.

    With several levels, the input states of each round are accepted outputs of rounds
    one level below, and level 1 uses noisy :math:`T\ket{+}` states.

    Circuit taken from Fig. 8 of:
    https://journals.aps.org/prxquantum/pdf/10.1103/PRXQuantum.2.020341

    Type parameters:
        Q: The code's logical qubit type.
        M: The code's logical measurement type.
        C: Type of the context passed to `prep_zero` and `qec`.
        BATCH_SIZE: Number of rounds run in the same batch.

    Attributes:
        ops: The code's operations used to implement each round.
        prep_zero: Prepares a qubit in the logical zero state, given the context.
        qec: Applies a QEC cycle to a qubit, given the context.
        qec_policy: When to apply `qec` to the qubits of a round.
        levels: Number of distillation levels, at least 1.
        max_attempts: Maximum number of rounds checked for each state before giving
            up, at every level.
        batch: Top-level rounds whose outcomes are unread. Provide an empty queue with
            `guppylang.std.collections.queue.empty_queue`.
    """

    ops: DistillationOps[Q, M]
    prep_zero: Function[[C], Q]  # type: ignore[type-arg,valid-type,misc]
    qec: Function[[C, Q], None]  # type: ignore[type-arg,valid-type]
    qec_policy: DistillationQECPolicy
    levels: int
    max_attempts: int
    batch: Queue[DistillationPreBlock[Q, M], BATCH_SIZE]

    @guppy
    @no_type_check
    def get_state(self, context: C) -> Q:
        """Return a distilled state, running `BATCH_SIZE` rounds at a time when no
        unchecked round is left.

        Args:
            context: Passed to `prep_zero` and `qec` in each round.
        """
        if BATCH_SIZE <= 0:  # type: ignore[misc]
            panic("DistillationFactory: BATCH_SIZE must be greater than zero")
        levels = self.levels
        if levels < 1:
            panic("DistillationFactory: levels must be at least 1")

        for _ in range(self.max_attempts):
            if len(self.batch) == 0:
                for _ in range(BATCH_SIZE):  # type: ignore[misc]
                    pre_block = self._round(levels, context)
                    self.batch.push(pre_block)

            state = self.batch.pop().force_check()
            if state.is_some():
                return state.unwrap()
            else:
                state.unwrap_nothing()

        exit("DistillationFactory ran out of attempts!")
        # Unreachable, but required by the Guppy checker
        return self.batch.pop().force_check().unwrap()

    @guppy
    @no_type_check
    def discard(self: Self @ owned) -> None:
        """Discard all unchecked rounds in the batch."""
        for pre_block in self.batch:
            pre_block.discard()

    @guppy
    @no_type_check
    def _round(self, level: int, context: C) -> DistillationPreBlock[Q, M]:
        """Run one round of `level` without reading its X-basis outcomes."""
        costs = self.qec_policy
        qs = array(self.prep_zero(context) for _ in range(comptime(_N_BLOCKS)))
        counters = array(0.0 for _ in range(comptime(_N_BLOCKS)))
        for i in range(comptime(_N_BLOCKS)):
            self._charge(context, qs, counters, i, costs.prep_zero)

        for i in comptime(_PLUS_IDXS):
            self.ops.h(qs[i])
            self._charge(context, qs, counters, i, costs.h)
        for c, t in comptime(_ENCODER_CX_PAIRS):
            self.ops.cx(qs[c], qs[t])
            self._charge(context, qs, counters, c, costs.cx)
            self._charge(context, qs, counters, t, costs.cx)

        for j in range(1, comptime(_N_BLOCKS)):
            if level == 1:
                t_state = self.ops.prep_noisy_t()
            else:
                t_state = self._accepted(level - 1, context)
            _inject_tdg(self.ops, qs[j], t_state)
            self._charge(context, qs, counters, j, costs.inject_tdg)
            self.ops.h(qs[j])
            self._charge(context, qs, counters, j, costs.h)

        outcomes = array(
            self.ops.measure_z(qs.take(i + 1)) for i in range(comptime(_N_OUTCOMES))
        )
        out = qs.take(0)
        qs.discard_all_taken()

        return DistillationPreBlock(out, self.ops, outcomes)

    @guppy
    @no_type_check
    def _accepted(self, level: int, context: C) -> Q:
        """Run rounds of `level` one at a time until one passes its checks."""
        for _ in range(self.max_attempts):
            state = self._round(level, context).force_check()
            if state.is_some():
                return state.unwrap()
            state.unwrap_nothing()
        exit("DistillationFactory ran out of attempts!")
        # Unreachable, but required by the Guppy checker
        return self.ops.prep_noisy_t()

    @guppy
    @no_type_check
    def _charge(
        self,
        context: C,
        qs: array[Q, comptime(_N_BLOCKS)],
        counters: array[float, comptime(_N_BLOCKS)],
        i: int,
        cost: float,
    ) -> None:
        counters[i] = counters[i] + cost
        if counters[i] >= self.qec_policy.threshold:
            self.qec(context, qs[i])
            counters[i] = 0.0
