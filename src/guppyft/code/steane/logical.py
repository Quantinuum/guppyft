"""Guppy functions for the logical operations and types for the Steane QEC architecture.

This module contains bindings for the fundamental ops in the HUGR extensions, as well
as composite operations that comprise multiple logical operations.

The physical implementation for these ops is provided in
:py:mod:`~guppyft.code.steane.primitives`.
"""

from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.lang import owned
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import tys as ht
from hugr.ops import DataflowOp, ExtOp

from guppyft.extensions import steane_ops, steane_types

_OPS_EXTN = steane_ops()


def _steane_op(
    op_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(_OPS_EXTN.get_op(op_name), ty, [arg.to_hugr(ctx) for arg in inst])

    return op


@custom_type(steane_types.steane_measurement(), copyable=True, droppable=True)
class Measurement:
    """A measurement outcome of a logical Steane qubit."""

    @hugr_op(_steane_op("decode"))
    @no_type_check
    def decode(self: "Measurement") -> bool:
        """Return the decoded logical measurement outcome."""


@custom_type(steane_types.steane_qubit(), copyable=False, droppable=False)
class Qubit:
    """A logical qubit encoded in the Steane code.

    Constructing a ``Qubit`` instance prepares it in the logical zero state.
    """

    @hugr_op(_steane_op("prep_zero"))
    @no_type_check
    def __new__() -> "Qubit": ...

    @guppy
    @no_type_check
    def free(self: "Qubit" @ owned) -> None:
        """Free the qubit."""
        free(self)

    @guppy
    @no_type_check
    def measure_z(self: "Qubit" @ owned) -> Measurement:
        """Destructive measurement of the qubit in the Z basis."""
        return measure_z(self)

    @guppy
    @no_type_check
    def qec_cycle(self: "Qubit") -> None:
        """Perform a QEC cycle on the logical qubit."""
        qec_cycle(self)

    @guppy
    @no_type_check
    def x(self: "Qubit") -> None:
        """X gate."""
        x(self)

    @guppy
    @no_type_check
    def y(self: "Qubit") -> None:
        """Y gate."""
        y(self)

    @guppy
    @no_type_check
    def z(self: "Qubit") -> None:
        """Z gate."""
        z(self)

    @guppy
    @no_type_check
    def h(self: "Qubit") -> None:
        """H gate."""
        h(self)

    @guppy
    @no_type_check
    def s(self: "Qubit") -> None:
        """S gate."""
        s(self)

    @guppy
    @no_type_check
    def sdg(self: "Qubit") -> None:
        """Sdg gate."""
        sdg(self)

    @guppy
    def t(self: "Qubit") -> None:
        r"""Apply a logical :math:`T` gate using magic-state injection."""
        t(self)

    @guppy
    def tdg(self: "Qubit") -> None:
        r"""Apply a logical :math:`T^\dagger` gate using magic-state injection."""
        tdg(self)


@hugr_op(_steane_op("free"))
@no_type_check
def free(qubit: "Qubit" @ owned) -> None:
    """Free a qubit."""


@hugr_op(_steane_op("measure_z"))
@no_type_check
def measure_z(qubit: "Qubit" @ owned) -> Measurement:
    """Destructive measurement of the qubit in the Z basis."""


@hugr_op(_steane_op("qec_cycle"))
@no_type_check
def qec_cycle(qubit: Qubit) -> None:
    """Perform a QEC cycle on the logical qubit."""


@hugr_op(_steane_op("x"))
@no_type_check
def x(qubit: Qubit) -> None:
    """X gate."""


@hugr_op(_steane_op("y"))
@no_type_check
def y(qubit: Qubit) -> None:
    """Y gate."""


@hugr_op(_steane_op("z"))
@no_type_check
def z(qubit: "Qubit") -> None:
    """Z gate."""


@hugr_op(_steane_op("h"))
@no_type_check
def h(qubit: "Qubit") -> None:
    """H gate."""


@hugr_op(_steane_op("s"))
@no_type_check
def s(qubit: "Qubit") -> None:
    """S gate."""


@hugr_op(_steane_op("sdg"))
@no_type_check
def sdg(qubit: "Qubit") -> None:
    """Sdg gate."""


@hugr_op(_steane_op("prep_t_state"))
@no_type_check
def prep_t_state() -> "Qubit":
    r"""Prepare a logical :math:`T\ket{+}` magic state for :math:`T` and
    :math:`T^\dagger` injection."""


@hugr_op(_steane_op("inject_t"))
@no_type_check
def inject_t(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    """Apply a logical :math:`T` gate by consuming a magic-state qubit."""


@hugr_op(_steane_op("inject_tdg"))
@no_type_check
def inject_tdg(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    r"""Apply a logical :math:`T^\dagger` gate by consuming a magic-state qubit."""


@hugr_op(_steane_op("cx"))
@no_type_check
def cx(q0: "Qubit", q1: "Qubit") -> None:
    """CX gate."""


@hugr_op(_steane_op("cz"))
@no_type_check
def cz(q0: "Qubit", q1: "Qubit") -> None:
    """CZ gate."""


@hugr_op(_steane_op("swap"))
@no_type_check
def swap(q0: "Qubit", q1: "Qubit") -> None:
    """SWAP gate."""


@guppy
def t(q: Qubit) -> None:
    r"""Apply a logical :math:`T` gate using magic-state injection."""
    a = prep_t_state()
    inject_t(q, a)


@guppy
def tdg(q: Qubit) -> None:
    r"""Apply a logical :math:`T^\dagger` gate using magic-state injection."""
    a = prep_t_state()
    inject_tdg(q, a)
