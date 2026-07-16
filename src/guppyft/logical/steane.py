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
from guppyft.logical.std import LogicalMeasurement

OPS_EXTN = steane_ops()
TYPES_EXTN = steane_types()

qubit_type = steane_types.steane_qubit()


def steane_op(
    op_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(OPS_EXTN.get_op(op_name), ty, [arg.to_hugr(ctx) for arg in inst])

    return op


@custom_type(qubit_type, copyable=False, droppable=False)
class Qubit:
    @hugr_op(steane_op("prep_zero"))
    @no_type_check
    def __new__() -> "Qubit": ...

    @guppy
    @no_type_check
    def free(self: "Qubit" @ owned) -> None:
        """Free the qubit."""
        free(self)

    @guppy
    @no_type_check
    def measure_z(self: "Qubit" @ owned) -> LogicalMeasurement[1]:
        """Destructive measurement of the qubit in the Z basis."""
        return measure_z(self)

    @guppy
    @no_type_check
    def x(self: "Qubit") -> None:
        """X gate."""
        x(self)

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
    @no_type_check
    def inject_magic_for_t(self: "Qubit", magic: "Qubit" @ owned) -> None:
        """Perform a T gate by injecting a magic state."""
        inject_magic_for_t(self, magic)

    @guppy
    @no_type_check
    def inject_magic_for_tdg(self: "Qubit", magic: "Qubit" @ owned) -> None:
        """Perform a Tdg gate by injecting a magic state."""
        inject_magic_for_tdg(self, magic)


@hugr_op(steane_op("free"))
@no_type_check
def free(qubit: "Qubit" @ owned) -> None:
    """Free q qubit."""


@hugr_op(steane_op("measure_z"))
@no_type_check
def measure_z(self: "Qubit" @ owned) -> LogicalMeasurement[1]:
    """Destructive measurement of the qubit in the Z basis."""


@hugr_op(steane_op("x"))
@no_type_check
def x(qubit: Qubit) -> None:
    """X gate."""


@hugr_op(steane_op("z"))
@no_type_check
def z(qubit: "Qubit") -> None:
    """Z gate."""


@hugr_op(steane_op("h"))
@no_type_check
def h(qubit: "Qubit") -> None:
    """H gate."""


@hugr_op(steane_op("s"))
@no_type_check
def s(qubit: "Qubit") -> None:
    """S gate."""


@hugr_op(steane_op("sdg"))
@no_type_check
def sdg(qubit: "Qubit") -> None:
    """Sdg gate."""


@hugr_op(steane_op("prep_magic_for_t_like"))
@no_type_check
def prep_magic_for_t_like() -> "Qubit":
    """Prepare a magic state that can be used to produce T-like states (T and Tdg)."""


@hugr_op(steane_op("inject_magic_for_t"))
@no_type_check
def inject_magic_for_t(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    """Perform a T gate by injecting a magic state."""


@hugr_op(steane_op("inject_magic_for_t"))
@no_type_check
def inject_magic_for_tdg(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    """Perform a Tdg gate by injecting a magic state."""


@hugr_op(steane_op("cx"))
@no_type_check
def cx(q0: "Qubit", q1: "Qubit") -> None:
    """CX gate."""


@hugr_op(steane_op("swap"))
@no_type_check
def swap(q0: "Qubit", q1: "Qubit") -> None:
    """SWAP gate."""
