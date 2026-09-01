from collections.abc import Callable, Sequence
from typing import Generic, TypeVar, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.lang import owned
from guppylang.std.option import Option
from guppylang.std.quantum import Measurement
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys.arg import Argument, ConstArg
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import NumericType
from hugr import tys as ht
from hugr.ext import TypeDef
from hugr.ops import DataflowOp, ExtOp

from guppyft.extensions import iceberg_ops, iceberg_types
from guppyft.std import LogicalMeasurement

_OPS_EXTN = iceberg_ops()


def _iceberg_op(
    op_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(_OPS_EXTN.get_op(op_name), ty, [arg.to_hugr(ctx) for arg in inst])

    return op


T = TypeVar("T")


def _custom_block_type(block_ty_def: TypeDef) -> Callable[[type[T]], type[T]]:
    def to_hugr_ty(args: Sequence[Argument], ctx: ToHugrContext) -> ht.Type:
        [k_arg] = args
        assert isinstance(k_arg, ConstArg)
        return ht.ExtType(block_ty_def, [k_arg.to_hugr(ctx)])

    return custom_type(
        to_hugr_ty,
        copyable=False,
        droppable=False,
        params=[ConstParam(1, "k", NumericType(NumericType.Kind.Nat))],
    )


N = guppy.nat_var("N")
M = guppy.nat_var("M")


@_custom_block_type(iceberg_types.iceberg_block_def)
class Block(Generic[N]):  # type: ignore[misc]
    @hugr_op(_iceberg_op("alloc_zero"))
    @no_type_check
    def __new__() -> "Block[N]": ...

    @guppy
    @no_type_check
    def x(self: "Block[N]", i: int) -> None:
        """X gate on the qubit with index `i`."""
        x(self, i)

    @guppy
    @no_type_check
    def y(self: "Block[N]", i: int) -> None:
        """Y gate on the qubit with index `i`."""
        y(self, i)

    @guppy
    @no_type_check
    def z(self: "Block[N]", i: int) -> None:
        """Z gate on the qubit with index `i`."""
        z(self, i)

    @guppy
    @no_type_check
    def xx(self: "Block[N]", i: int, j: int) -> None:
        """X gate on the qubits with indices `i` and `j`."""
        xx(self, i, j)

    @guppy
    @no_type_check
    def yy(self: "Block[N]", i: int, j: int) -> None:
        """Y gate on the qubits with indices `i` and `j`."""
        yy(self, i, j)

    @guppy
    @no_type_check
    def zz(self: "Block[N]", i: int, j: int) -> None:
        """Z gate on the qubits with indices `i` and `j`."""
        zz(self, i, j)

    @guppy
    @no_type_check
    def all_but_one_x(self: "Block[N]", i: int) -> None:
        """X gate on all qubits except that with index `i`."""
        all_but_one_x(self, i)

    @guppy
    @no_type_check
    def all_but_one_z(self: "Block[N]", i: int) -> None:
        """Z gate on all qubits except that with index `i`."""
        all_but_one_z(self, i)

    @guppy
    @no_type_check
    def all_x(self: "Block[N]") -> None:
        """X gate on all qubits."""
        all_x(self)

    @guppy
    @no_type_check
    def all_y(self: "Block[N]") -> None:
        """Y gate on all qubits."""
        all_y(self)

    @guppy
    @no_type_check
    def all_z(self: "Block[N]") -> None:
        """Z gate on all qubits."""
        all_z(self)

    @guppy
    @no_type_check
    def x_with_all_but_one_z(self: "Block[N]", i: int) -> None:
        """X gate on the qubit with index `i`; Z on all others."""
        x_with_all_but_one_z(self, i)

    @guppy
    @no_type_check
    def z_with_all_but_one_x(self: "Block[N]", i: int) -> None:
        """Z gate on the qubit with index `i`; X on all others."""
        z_with_all_but_one_x(self, i)

    @guppy
    @no_type_check
    def fan_out(self: "Block[N]", i: int) -> None:
        """Fan-out from the qubit with index `i` to all others."""
        fan_out(self, i)

    @guppy
    @no_type_check
    def fan_in(self: "Block[N]", i: int) -> None:
        """Fan-in to the qubit with index `i` from all others."""
        fan_in(self, i)

    @guppy
    @no_type_check
    def rx(self: "Block[N]", i: int, phase: float) -> None:
        """Rx rotation of `phase` radians on the qubit with index `i`."""
        rx(self, i, phase)

    @guppy
    @no_type_check
    def ry(self: "Block[N]", i: int, phase: float) -> None:
        """Ry rotation of `phase` radians on the qubit with index `i`."""
        ry(self, i, phase)

    @guppy
    @no_type_check
    def rz(self: "Block[N]", i: int, phase: float) -> None:
        """Rz rotation of `phase` radians on the qubit with index `i`."""
        rz(self, i, phase)

    @guppy
    @no_type_check
    def all_rx(self: "Block[N]", phase: float) -> None:
        """Rx rotation of `phase` radians on all qubits."""
        all_rx(self, phase)

    @guppy
    @no_type_check
    def all_ry(self: "Block[N]", phase: float) -> None:
        """Ry rotation of `phase` radians on all qubits."""
        all_ry(self, phase)

    @guppy
    @no_type_check
    def all_rz(self: "Block[N]", phase: float) -> None:
        """Rz rotation of `phase` radians on all qubits."""
        all_rz(self, phase)

    @guppy
    @no_type_check
    def all_but_one_rx(self: "Block[N]", i: int, phase: float) -> None:
        """Rx rotation of `phase` radians on qubits except that with index `i`."""
        all_but_one_rx(self, i, phase)

    @guppy
    @no_type_check
    def all_but_one_rz(self: "Block[N]", i: int, phase: float) -> None:
        """Rz rotation of `phase` radians on qubits except that with index `i`."""
        all_but_one_rz(self, i, phase)

    @guppy
    @no_type_check
    def all_h(self: "Block[N]") -> None:
        """H gate on all qubits."""
        all_h(self)

    @guppy
    @no_type_check
    def xx_phase(self: "Block[N]", i: int, j: int, phase: float) -> None:
        """XXPhase rotation of `phase` radians on the qubits with indices `i`
        and `j`."""
        xx_phase(self, i, j, phase)

    @guppy
    @no_type_check
    def yy_phase(self: "Block[N]", i: int, j: int, phase: float) -> None:
        """YYPhase rotation of `phase` radians on the qubits with indices `i`
        and `j`."""
        yy_phase(self, i, j, phase)

    @guppy
    @no_type_check
    def zz_phase(self: "Block[N]", i: int, j: int, phase: float) -> None:
        """ZZPhase rotation of `phase` radians on the qubits with indices `i`
        and `j`."""
        zz_phase(self, i, j, phase)

    @guppy
    @no_type_check
    def cx(self: "Block[N]", i: int, j: int) -> None:
        """CX gate on the qubits with indices `i` (control) and `j` (target)."""
        cx(self, i, j)

    @guppy
    @no_type_check
    def swap(self: "Block[N]", i: int, j: int) -> None:
        """Swap of the qubits with indices `i` and `j`."""
        swap(self, i, j)

    @guppy
    @no_type_check
    def measure_syndrome(self: "Block[N]") -> tuple[Measurement, Measurement]:
        """Syndrome measurement."""
        return measure_syndrome(self)

    @guppy
    @no_type_check
    def try_measure_one_x(self: "Block[N]", i: int) -> Option[Measurement]:
        """Fallible non-destructive measurement in the X basis of the qubit
        with index `i`."""
        return try_measure_one_x(self, i)

    @guppy
    @no_type_check
    def try_measure_one_z(self: "Block[N]", i: int) -> Option[Measurement]:
        """Fallible non-destructive measurement in the Z basis of the qubit
        with index `i`."""
        return try_measure_one_z(self, i)


@custom_type(iceberg_types.iceberg_qubit(), copyable=False, droppable=False)
class Qubit:
    @hugr_op(_iceberg_op("alloc_dynq"))
    @no_type_check
    def __new__() -> "Qubit": ...

    @guppy
    @no_type_check
    def x(self: "Qubit") -> None:
        """X gate."""
        x_dynq(self)

    @guppy
    @no_type_check
    def y(self: "Qubit") -> None:
        """Y gate."""
        y_dynq(self)

    @guppy
    @no_type_check
    def z(self: "Qubit") -> None:
        """Z gate."""
        z_dynq(self)

    @guppy
    @no_type_check
    def rx(self: "Qubit", phase: float) -> None:
        """Rx rotation of `phase` radians."""
        rx_dynq(self, phase)

    @guppy
    @no_type_check
    def ry(self: "Qubit", phase: float) -> None:
        """Ry rotation of `phase` radians."""
        ry_dynq(self, phase)

    @guppy
    @no_type_check
    def rz(self: "Qubit", phase: float) -> None:
        """Rz rotation of `phase` radians."""
        rz_dynq(self, phase)

    @guppy
    @no_type_check
    def try_measure_x(self: "Qubit") -> Option[Measurement]:
        """Fallible non-destructive measurement in the X basis."""
        return try_measure_x_dynq(self)

    @guppy
    @no_type_check
    def try_measure_z(self: "Qubit") -> Option[Measurement]:
        """Fallible non-destructive measurement in the Z basis."""
        return try_measure_z_dynq(self)


@_custom_block_type(iceberg_types.iceberg_borrowed_block_def)
class BorrowedBlock(Generic[N]):  # type: ignore[misc]
    @guppy
    @no_type_check
    def borrow_more(
        self: "BorrowedBlock[N]", indices: array[int, M]
    ) -> array[Qubit, M]:
        """Extract dynamic logical qubits from an already-borrowed block."""
        return borrow_more(self, indices)

    @guppy
    @no_type_check
    def restore_some(self: "BorrowedBlock[N]", qubits: array[Qubit, M] @ owned) -> None:
        """Restore some dynamic logical qubits to their originating block."""
        restore_some(self, qubits)


@_custom_block_type(iceberg_types.iceberg_pre_block_def)
class PreBlock(Generic[N]):  # type: ignore[misc]
    @hugr_op(_iceberg_op("try_alloc_zero"))
    @no_type_check
    def __new__() -> "PreBlock[N]": ...

    @hugr_op(_iceberg_op("check_pre_block"))
    @no_type_check
    def check(self: "PreBlock[N]" @ owned) -> Option[Block[N]]: ...


@hugr_op(_iceberg_op("x_d"))
@no_type_check
def x(block: Block[N], i: int) -> None:
    """X gate on the qubit with index `i`."""


@hugr_op(_iceberg_op("y_d"))
@no_type_check
def y(block: Block[N], i: int) -> None:
    """Y gate on the qubit with index `i`."""


@hugr_op(_iceberg_op("z_d"))
@no_type_check
def z(block: Block[N], i: int) -> None:
    """Z gate on the qubit with index `i`."""


@hugr_op(_iceberg_op("xx_d"))
@no_type_check
def xx(block: Block[N], i: int, j: int) -> None:
    """X gate on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("yy_d"))
@no_type_check
def yy(block: Block[N], i: int, j: int) -> None:
    """Y gate on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("zz_d"))
@no_type_check
def zz(block: Block[N], i: int, j: int) -> None:
    """Z gate on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("all_but_one_x_d"))
@no_type_check
def all_but_one_x(block: Block[N], i: int) -> None:
    """X gate on all qubits except that with index `i`."""


@hugr_op(_iceberg_op("all_but_one_z_d"))
@no_type_check
def all_but_one_z(block: Block[N], i: int) -> None:
    """Z gate on all qubits except that with index `i`."""


@hugr_op(_iceberg_op("all_x"))
@no_type_check
def all_x(block: Block[N]) -> None:
    """X gate on all qubits."""


@hugr_op(_iceberg_op("all_y"))
@no_type_check
def all_y(block: Block[N]) -> None:
    """Y gate on all qubits."""


@hugr_op(_iceberg_op("all_z"))
@no_type_check
def all_z(block: Block[N]) -> None:
    """Z gate on all qubits."""


@hugr_op(_iceberg_op("x_with_all_but_one_z_d"))
@no_type_check
def x_with_all_but_one_z(block: Block[N], i: int) -> None:
    """X gate on the qubit with index `i`; Z on all others."""


@hugr_op(_iceberg_op("z_with_all_but_one_x_d"))
@no_type_check
def z_with_all_but_one_x(block: Block[N], i: int) -> None:
    """Z gate on the qubit with index `i`; X on all others."""


@hugr_op(_iceberg_op("fan_out_d"))
@no_type_check
def fan_out(block: Block[N], i: int) -> None:
    """Fan-out from the qubit with index `i` to all others."""


@hugr_op(_iceberg_op("fan_in_d"))
@no_type_check
def fan_in(block: Block[N], i: int) -> None:
    """Fan-in to the qubit with index `i` from all others."""


@hugr_op(_iceberg_op("rx_d"))
@no_type_check
def rx(block: Block[N], i: int, phase: float) -> None:
    """Rx rotation of `phase` radians on the qubit with index `i`."""


@hugr_op(_iceberg_op("ry_d"))
@no_type_check
def ry(block: Block[N], i: int, phase: float) -> None:
    """Ry rotation of `phase` radians on the qubit with index `i`."""


@hugr_op(_iceberg_op("rz_d"))
@no_type_check
def rz(block: Block[N], i: int, phase: float) -> None:
    """Rz rotation of `phase` radians on the qubit with index `i`."""


@hugr_op(_iceberg_op("all_rx"))
@no_type_check
def all_rx(block: Block[N], phase: float) -> None:
    """Rx gate on all qubits."""


@hugr_op(_iceberg_op("all_ry"))
@no_type_check
def all_ry(block: Block[N], phase: float) -> None:
    """Ry gate on all qubits."""


@hugr_op(_iceberg_op("all_rz"))
@no_type_check
def all_rz(block: Block[N], phase: float) -> None:
    """Rz gate on all qubits."""


@hugr_op(_iceberg_op("all_but_one_rx_d"))
@no_type_check
def all_but_one_rx(block: Block[N], i: int, phase: float) -> None:
    """Rx rotation of `phase` radians on qubits except that with index `i`."""


@hugr_op(_iceberg_op("all_but_one_rz_d"))
@no_type_check
def all_but_one_rz(block: Block[N], i: int, phase: float) -> None:
    """Rz rotation of `phase` radians on qubits except that with index `i`."""


@hugr_op(_iceberg_op("all_h"))
@no_type_check
def all_h(block: Block[N]) -> None:
    """H gate on all qubits."""


@hugr_op(_iceberg_op("xx_phase_d"))
@no_type_check
def xx_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """XXPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("yy_phase_d"))
@no_type_check
def yy_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """YYPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("zz_phase_d"))
@no_type_check
def zz_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """ZZPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("cx_d"))
@no_type_check
def cx(block: Block[N], i: int, j: int) -> None:
    """CX gate on the qubits with indices `i` (control) and `j` (target)."""


@hugr_op(_iceberg_op("swap_d"))
@no_type_check
def swap(block: Block[N], i: int, j: int) -> None:
    """Swap of the qubits with indices `i` and `j`."""


@hugr_op(_iceberg_op("xx_phase_between_blocks_d"))
@no_type_check
def xx_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """XXPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(_iceberg_op("yy_phase_between_blocks_d"))
@no_type_check
def yy_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """YYPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(_iceberg_op("zz_phase_between_blocks_d"))
@no_type_check
def zz_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """ZZPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(_iceberg_op("cx_between_blocks_d"))
@no_type_check
def cx_between_blocks(block0: Block[N], block1: Block[N], i0: int, i1: int) -> None:
    """CX gate on the qubit with index `i0` in block `block0` and the qubit with
    index `i1` in block `block1`."""


@hugr_op(_iceberg_op("cx_transversal"))
@no_type_check
def cx_transversal(block0: Block[N], block1: Block[N]) -> None:
    """CX gate applied transversally over `block0` and `block1`."""


@hugr_op(_iceberg_op("free"))
@no_type_check
def discard(block: Block[N] @ owned) -> None:
    """Free `block`."""


@hugr_op(_iceberg_op("measure_syndrome"))
@no_type_check
def measure_syndrome(block: Block[N]) -> tuple[Measurement, Measurement]:
    """Syndrome measurement."""


@hugr_op(_iceberg_op("measure_all"))
@no_type_check
def measure_all(block: Block[N] @ owned) -> LogicalMeasurement[N]:
    """Destructive measurement of all qubits in `block`."""


@hugr_op(_iceberg_op("try_measure_one_x_d"))
@no_type_check
def try_measure_one_x(block: Block[N], i: int) -> Option[Measurement]:
    """Fallible non-destructive measurement in the X basis of the qubit with
    index `i`."""


@hugr_op(_iceberg_op("try_measure_one_z_d"))
@no_type_check
def try_measure_one_z(block: Block[N], i: int) -> Option[Measurement]:
    """Fallible non-destructive measurement in the Z basis of the qubit with
    index `i`."""


@hugr_op(_iceberg_op("try_alloc_dynq"))
@no_type_check
def try_alloc_dynq() -> Option[Qubit]:
    """Fallible allocation of a qubit in the zero state."""


@hugr_op(_iceberg_op("free_dynq"))
@no_type_check
def free_dynq(qubit: Qubit @ owned) -> None:
    """Free `qubit`."""


@hugr_op(_iceberg_op("x_dynq"))
@no_type_check
def x_dynq(qubit: Qubit) -> None:
    """X gate."""


@hugr_op(_iceberg_op("y_dynq"))
@no_type_check
def y_dynq(qubit: Qubit) -> None:
    """Y gate."""


@hugr_op(_iceberg_op("z_dynq"))
@no_type_check
def z_dynq(qubit: Qubit) -> None:
    """Z gate."""


@hugr_op(_iceberg_op("rx_dynq"))
@no_type_check
def rx_dynq(qubit: Qubit, phase: float) -> None:
    """Rx rotation of `phase` radians."""


@hugr_op(_iceberg_op("ry_dynq"))
@no_type_check
def ry_dynq(qubit: Qubit, phase: float) -> None:
    """Ry rotation of `phase` radians."""


@hugr_op(_iceberg_op("rz_dynq"))
@no_type_check
def rz_dynq(qubit: Qubit, phase: float) -> None:
    """Rz rotation of `phase` radians."""


@hugr_op(_iceberg_op("try_measure_x_dynq"))
@no_type_check
def try_measure_x_dynq(qubit: Qubit) -> Option[Measurement]:
    """Fallible non-destructive measurement in the X basis."""


@hugr_op(_iceberg_op("try_measure_z_dynq"))
@no_type_check
def try_measure_z_dynq(qubit: Qubit) -> Option[Measurement]:
    """Fallible non-destructive measurement in the Z basis."""


@hugr_op(_iceberg_op("xx_phase_dynq"))
@no_type_check
def xx_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """XXPhase rotation of `phase` radians on two qubits."""


@hugr_op(_iceberg_op("yy_phase_dynq"))
@no_type_check
def yy_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """YYPhase rotation of `phase` radians on two qubits."""


@hugr_op(_iceberg_op("zz_phase_dynq"))
@no_type_check
def zz_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """ZZPhase rotation of `phase` radians on two qubits."""


@hugr_op(_iceberg_op("cx_dynq"))
@no_type_check
def cx_dynq(qubit0: Qubit, qubit1: Qubit) -> None:
    """CX gate on `qubit0` (control) and `qubit1` (target)."""


@hugr_op(_iceberg_op("borrow"))
@no_type_check
def borrow(
    block: Block[N] @ owned, indices: array[int, M]
) -> (BorrowedBlock[N], array[Qubit, M]):
    """Extract dynamic logical qubits from a block."""


@hugr_op(_iceberg_op("borrow_more"))
@no_type_check
def borrow_more(block: BorrowedBlock[N], indices: array[int, M]) -> array[Qubit, M]:
    """Extract additional dynamic logical qubits from an already-borrowed block."""


@hugr_op(_iceberg_op("restore_some"))
@no_type_check
def restore_some(block: BorrowedBlock[N], qubits: array[Qubit, M] @ owned) -> None:
    """Restore some dynamic logical qubits to their originating block."""


@hugr_op(_iceberg_op("restore"))
@no_type_check
def restore(
    block: BorrowedBlock[N] @ owned, qubits: array[Qubit, M] @ owned
) -> Block[N]:
    """Restore all remaining dynamic logical qubits to their originating block."""
