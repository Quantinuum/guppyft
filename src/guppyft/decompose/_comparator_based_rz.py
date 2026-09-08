"""Approximate Rz rotation with logarithmic Toffoli count.

This is a duplicate of the `comparator_based_rz.py` module in guppy-algos.
This is a temporary solution to avoid circular imports. We will remove when
we find the right place for this to live
See: https://github.com/quantinuum-dev/guppyft/issues/272.

Reference: https://arxiv.org/pdf/2404.05618
Original contribution: @vvandaele (Vivien Vandaele)
"""
# mypy: ignore-errors

from math import ceil, log2
from typing import no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.angles import angle
from guppylang.std.builtins import Function, array, comptime, nat
from guppylang.std.lang import Drop
from guppylang.std.quantum import (
    cx,
    cz,
    discard_array,
    h,
    measure,
    project_z,
    qubit,
    s,
    sdg,
    t,
    tdg,
    toffoli,
    x,
    z,
)

from guppyft._math import floor, get_bit, tan


@guppy
@no_type_check
def temp_and_uncompute(q_0: qubit, q_1: qubit, target_q: qubit) -> None:
    """Uncompute the temporary AND operation.

    This function reverses the effects of the AND operation
    applied to the input qubits and the target qubit. It is equivalent to
    measurement based uncomputation as described in Fig 4.
    https://arxiv.org/pdf/1805.03662. The qubit must be discarded after use.

    Args:
        q_0 (qubit): The first input qubit.
        q_1 (qubit): The second input qubit.
        target_q (qubit): The auxiliary qubit used in computation.

    """
    h(target_q)
    # TODO: project_z is wasteful in a QEC setting, since measurements of
    # blocks are destructive. Hence, `project_z` causes the block to be
    # prepared again in the |0> state, but this is discarded immediately after.
    if project_z(target_q).read():
        cz(q_0, q_1)


@guppy
@no_type_check
def temp_and_compute(q0: qubit, q1: qubit, t_qubit: qubit) -> None:
    r"""Temporary AND computation acting on 0 state target.

    Following the construction in https://arxiv.org/abs/1805.03662
    which uses 4 T-gates.

    Args:
        q0 (qubit): The first input qubit.
        q1 (qubit): The second input qubit.
        t_qubit (qubit): The target qubit to store the result. Begins in :math:`\ket{0}`

    """
    # Prepare T|+> state
    # TODO: It would be best to lower this to a single T state prep rather than
    #  inject it...
    h(t_qubit)
    t(t_qubit)

    # Consume it to implement the AND operation
    cx(q1, t_qubit)
    tdg(t_qubit)
    cx(q0, t_qubit)
    t(t_qubit)
    cx(q1, t_qubit)
    tdg(t_qubit)
    h(t_qubit)
    sdg(t_qubit)


@guppy.protocol
class ConstantComparator[n: nat, n_ancillas: nat]:
    """A constant comparison acting on RUS and workspace registers.

    Type parameters:
        n: Number of qubits in the input register being compared.
        n_ancillas: Number of workspace qubits required by the comparator.

    """

    @guppy.require
    @no_type_check
    def compose(
        self,
        a: array[qubit, n],
        b: array[qubit, n_ancillas],
        target: qubit,
        k: int,
    ) -> None:
        """Compare the input register against the classical constant ``k``.

        Args:
            a: The ``n``-qubit input register interpreted as an integer.
            b: The ``n_ancillas``-qubit workspace register used by the
                comparator implementation.
            target: Qubit on which to accumulate the comparison result.
            k: Classical integer against which ``a`` is compared.

        """


@guppy.struct(frozen=True)
class ConstantComparatorCascade[n: nat, n_ancillas: nat]:
    """Constant comparator configured with its AND operations and direction."""

    comp_and_op: Function[[qubit, qubit, qubit], None]
    uncomp_and_op: Function[[qubit, qubit, qubit], None]
    dagger: bool

    @guppy
    @no_type_check
    def _apply_x_gates(
        self,
        a: array[qubit, n],
        target: qubit,
        k: int,
    ) -> None:
        """Apply the comparator's constant-dependent X gates."""
        for i in range(n):
            if not get_bit(k, i):
                x(a[i])

        if not get_bit(k, comptime(n - 1)):
            x(target)

    @guppy
    @no_type_check
    def _apply_toffoli_ladder(
        self,
        a: array[qubit, n],
        b: array[qubit, n_ancillas],
        target: qubit,
        k: int,
    ) -> None:
        """Apply or unapply the comparator's Toffoli ladder."""
        if self.dagger:
            toffoli(b[comptime(n - 3)], a[comptime(n - 1)], target)
            for i in range(comptime(n - 2), 1, -1):
                if get_bit(k, i + 1) != get_bit(k, i):
                    x(b[i - 1])
                self.uncomp_and_op(b[i - 2], a[i], b[i - 1])
            if get_bit(k, 2) != get_bit(k, 1):
                x(b[0])
            if get_bit(k, 0):
                self.uncomp_and_op(a[0], a[1], b[0])
            elif get_bit(k, 1):
                cx(a[1], b[0])
        else:
            if get_bit(k, 0):
                self.comp_and_op(a[0], a[1], b[0])
            elif get_bit(k, 1):
                cx(a[1], b[0])
            if get_bit(k, 2) != get_bit(k, 1):
                x(b[0])
            for i in range(2, comptime(n - 1)):
                self.comp_and_op(b[i - 2], a[i], b[i - 1])
                if get_bit(k, i + 1) != get_bit(k, i):
                    x(b[i - 1])
            toffoli(b[comptime(n - 3)], a[comptime(n - 1)], target)

    @guppy
    @no_type_check
    def compose(
        self,
        a: array[qubit, n],
        b: array[qubit, n_ancillas],
        target: qubit,
        k: int,
    ) -> None:
        """Compare ``a`` against ``k``."""
        if self.dagger:
            self._apply_toffoli_ladder(a, b, target, k)
            self._apply_x_gates(a, target, k)
        else:
            self._apply_x_gates(a, target, k)
            self._apply_toffoli_ladder(a, b, target, k)


@guppy.struct(frozen=True)
class ComparatorBasedRz[
    n: nat,
    n_ancillas: nat,
    ComparatorType: (
        ConstantComparator[  # ty: ignore[invalid-type-variable-constraints]
            n, n_ancillas
        ],
        Drop,
    ),
]:
    r"""Apply an approximate :math:`R_z` rotation using comparator-based RUS.

    Implements Algorithm 1 from arXiv:2404.05618, "Single-qubit rotation
    algorithm with logarithmic Toffoli count and gate depth". The algorithm
    uses a repeat-until-success approach to approximate :math:`R_z(\theta)` within
    error :math:`\varepsilon`. Its success probability is greater than :math:`1/2`.

    Algorithm:

    1. Compute :math:`n = 1 + \lceil \log_2(1/\varepsilon) \rceil` and
       :math:`k = 2^{n-1} + \lfloor 2^{n-1} \tan(\theta/2) + 1/2 \rfloor`.
    2. Prepare register :math:`a` in superposition :math:`|+\rangle^{\otimes n}`.
    3. Perform the comparison :math:`a \geq k` on the target qubit.
    4. Apply an :math:`S` gate to the target qubit.
    5. Apply the inverse comparison to the target qubit.
    6. Measure register :math:`a`: if all results are zero, succeed; otherwise apply
       :math:`Z` and retry.

    This struct is generic over the comparator method: any concrete type that
    implements the :class:`ConstantComparator` protocol can be used. The
    comparator owns the details of the constant comparison, while
    ``n_ancillas`` captures the workspace required by that implementation. The
    :class:`ConstantComparatorCascade` implementation is the concrete cascade
    example from the paper and realizes the comparison with Clifford+Toffoli
    operations.

    Attributes:
        comparator: Configured forward constant comparator.
        inverse_comparator: Configured inverse constant comparator.

    """

    comparator: ComparatorType
    inverse_comparator: ComparatorType

    @guppy
    @no_type_check
    def compose(self, target: qubit, theta: angle) -> None:
        """Apply an approximate Rz rotation to ``target``."""
        half_pi = 1.57079632679489661923e0
        theta_float = float(theta)
        theta_reduced = theta_float - floor(theta_float / half_pi) * half_pi
        remainder = floor(theta_float / half_pi) % 4

        if remainder > 1:
            z(target)
        if remainder & 1 == 1:
            s(target)

        if theta_reduced == 0.0:
            return

        power = 2 ** (n - 1)
        k = power + floor(float(power) * tan(theta_reduced / 2.0) + 0.5)
        attempts = 0

        while True:
            attempts += 1
            a_reg = array(qubit() for _ in range(n))
            b_reg = array(qubit() for _ in range(n_ancillas))

            for i in range(n):
                h(a_reg[i])

            self.comparator.compose(a_reg, b_reg, target, k)
            s(target)
            self.inverse_comparator.compose(a_reg, b_reg, target, k)
            discard_array(b_reg)

            for i in range(n):
                h(a_reg[i])

            all_zero = True
            for q in a_reg:
                if measure(q).read():
                    all_zero = False

            if all_zero:
                break
            z(target)


def comparator_based_rz_cascade(
    epsilon: float,
) -> GuppyFunctionDefinition[[qubit, angle], None]:
    """Build a comparator-based Rz using the cascade comparator.

    This is a convenience function that constructs a :class:`ComparatorBasedRz`
    using the :class:`ConstantComparatorCascade` implementation. The returned
    function uses temporary AND compute and uncompute operations.

    Args:
        epsilon: Approximation error bound in operator norm.

    Returns:
        A Guppy function with signature ``(target: qubit, theta: angle) -> None``.
        The returned function uses temporary AND compute and uncompute operations.

    """
    n = 1 + ceil(log2(1 / epsilon))
    n_comparator_ancillas = n_constant_comparator_cascade_ancillas(n)

    @guppy
    @no_type_check
    def rz_fn(target: qubit, theta: angle) -> None:
        """Apply comparator-based Rz using temporary AND operations."""
        comparator = ConstantComparatorCascade[
            comptime(n), comptime(n_comparator_ancillas)
        ](
            temp_and_compute,
            temp_and_uncompute,
            False,
        )
        inverse_comparator = ConstantComparatorCascade[
            comptime(n), comptime(n_comparator_ancillas)
        ](
            temp_and_compute,
            temp_and_uncompute,
            True,
        )
        rz = ComparatorBasedRz(comparator, inverse_comparator)
        rz.compose(target, theta)

    return rz_fn


def n_constant_comparator_cascade_ancillas(n: int) -> int:
    """Return the workspace qubits required by the cascade comparator."""
    return n - 2


def n_comparator_based_rz_cascade_ancillas(epsilon: float) -> int:
    """Return total RUS and cascade-comparator ancillas for ``epsilon``."""
    n = 1 + ceil(log2(1 / epsilon))
    return n + n_constant_comparator_cascade_ancillas(n)
