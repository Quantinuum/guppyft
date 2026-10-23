"""Guppy functions and types for the Iceberg QEC architecture."""

from collections.abc import Callable, Sequence
from math import pi
from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, comptime
from guppylang.std.lang import owned
from guppylang.std.option import Option
from guppylang.std.quantum import Measurement
from guppylang_internals.decorator import custom_function, custom_type, hugr_op
from guppylang_internals.tys import Effect
from guppylang_internals.tys.arg import Argument, ConstArg
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.ty import NumericType
from hugr import tys as ht
from hugr.ext import TypeDef
from hugr.ops import ExtOp

from guppyft.code._util import BorrowRestoreCompiler, logical_op
from guppyft.extensions import iceberg_ops, iceberg_types
from guppyft.std import LogicalMeasurement


def _custom_block_type[T](block_ty_def: TypeDef) -> Callable[[type[T]], type[T]]:
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


def _borrow_restore_compiler(
    instantiate_op: Callable[[int, int], ExtOp],
) -> BorrowRestoreCompiler:
    """Instantiate Iceberg ops using the block size and the borrowed array length."""

    def op(m: int, owner_type: ht.ExtType) -> ExtOp:
        [k] = owner_type.args
        assert isinstance(k, ht.BoundedNatArg)
        return instantiate_op(k.n, m)

    return BorrowRestoreCompiler(op, iceberg_types.iceberg_qubit())


N = guppy.nat_var("N")
M = guppy.nat_var("M")


@_custom_block_type(iceberg_types.iceberg_block_def)
class Block(Generic[N]):  # type: ignore[misc]
    """An Iceberg logical block containing `N` logical qubits."""

    @hugr_op(logical_op(iceberg_ops.alloc_zero_def), effects=[Effect.ANY])
    @no_type_check
    def __new__() -> "Block[N]":
        """Allocate a block in the all-zero logical state."""

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
        """Ry rotation of `phase` radians, implemented using Rx and Rz."""
        ry(self, i, phase)

    @guppy
    @no_type_check
    def rz(self: "Block[N]", i: int, phase: float) -> None:
        """Rz rotation of `phase` radians on the qubit with index `i`."""
        rz(self, i, phase)

    @guppy
    @no_type_check
    def pauli_exp_all_x(self: "Block[N]", phase: float) -> None:
        r"""Apply the logical all-X Pauli exponential.

        .. math::

            \exp(-i \theta X^{\otimes k} / 2)

        where :math:`\theta` is ``phase`` in radians and :math:`k` is the
        number of logical qubits in the block.
        """
        pauli_exp_all_x(self, phase)

    @guppy
    @no_type_check
    def pauli_exp_all_y(self: "Block[N]", phase: float) -> None:
        r"""Apply the logical all-Y Pauli exponential.

        .. math::

            \exp(-i \theta Y^{\otimes k} / 2)

        where :math:`\theta` is ``phase`` in radians and :math:`k` is the
        number of logical qubits in the block.
        """
        pauli_exp_all_y(self, phase)

    @guppy
    @no_type_check
    def pauli_exp_all_z(self: "Block[N]", phase: float) -> None:
        r"""Apply the logical all-Z Pauli exponential.

        .. math::

            \exp(-i \theta Z^{\otimes k} / 2)

        where :math:`\theta` is ``phase`` in radians and :math:`k` is the
        number of logical qubits in the block.
        """
        pauli_exp_all_z(self, phase)

    @guppy
    @no_type_check
    def pauli_exp_all_x_except_at(self: "Block[N]", i: int, phase: float) -> None:
        r"""Apply the Pauli exponential with I at ``i`` and X elsewhere.

        .. math::

            \exp(-i \theta (
                X^{\otimes i} \otimes I \otimes X^{\otimes(k-i-1)}
            ) / 2)

        where :math:`\theta` is ``phase`` in radians and :math:`k` is the
        number of logical qubits in the block.
        """
        pauli_exp_all_x_except_at(self, i, phase)

    @guppy
    @no_type_check
    def pauli_exp_all_z_except_at(self: "Block[N]", i: int, phase: float) -> None:
        r"""Apply the Pauli exponential with I at ``i`` and Z elsewhere.

        .. math::

            \exp(-i \theta (
                Z^{\otimes i} \otimes I \otimes Z^{\otimes(k-i-1)}
            ) / 2)

        where :math:`\theta` is ``phase`` in radians and :math:`k` is the
        number of logical qubits in the block.
        """
        pauli_exp_all_z_except_at(self, i, phase)

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
    """A dynamic logical qubit from an Iceberg logical block."""

    @hugr_op(logical_op(iceberg_ops.alloc_dynq_def), effects=[Effect.ANY])
    @no_type_check
    def __new__() -> "Qubit":
        """Allocate a dynamic logical qubit."""

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
        """Ry rotation of `phase` radians, implemented using Rx and Rz."""
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
    """A borrowed Iceberg logical block."""

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
    """A candidate Iceberg logical block whose preparation may have failed."""

    @hugr_op(logical_op(iceberg_ops.try_alloc_zero_def), effects=[Effect.ANY])
    @no_type_check
    def __new__() -> "PreBlock[N]":
        """Attempt to allocate a block in the all-zero logical state."""

    @hugr_op(logical_op(iceberg_ops.check_pre_block_def))
    @no_type_check
    def check(self: "PreBlock[N]" @ owned) -> Option[Block[N]]:
        """Check whether state preparation succeeded."""


@hugr_op(logical_op(iceberg_ops.x_def))
@no_type_check
def x(block: Block[N], i: int) -> None:
    """X gate on the qubit with index `i`."""


@hugr_op(logical_op(iceberg_ops.y_def))
@no_type_check
def y(block: Block[N], i: int) -> None:
    """Y gate on the qubit with index `i`."""


@hugr_op(logical_op(iceberg_ops.z_def))
@no_type_check
def z(block: Block[N], i: int) -> None:
    """Z gate on the qubit with index `i`."""


@hugr_op(logical_op(iceberg_ops.xx_def))
@no_type_check
def xx(block: Block[N], i: int, j: int) -> None:
    """X gate on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.yy_def))
@no_type_check
def yy(block: Block[N], i: int, j: int) -> None:
    """Y gate on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.zz_def))
@no_type_check
def zz(block: Block[N], i: int, j: int) -> None:
    """Z gate on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.all_but_one_x_def))
@no_type_check
def all_but_one_x(block: Block[N], i: int) -> None:
    """X gate on all qubits except that with index `i`."""


@hugr_op(logical_op(iceberg_ops.all_but_one_z_def))
@no_type_check
def all_but_one_z(block: Block[N], i: int) -> None:
    """Z gate on all qubits except that with index `i`."""


@hugr_op(logical_op(iceberg_ops.all_x_def))
@no_type_check
def all_x(block: Block[N]) -> None:
    """X gate on all qubits."""


@hugr_op(logical_op(iceberg_ops.all_y_def))
@no_type_check
def all_y(block: Block[N]) -> None:
    """Y gate on all qubits."""


@hugr_op(logical_op(iceberg_ops.all_z_def))
@no_type_check
def all_z(block: Block[N]) -> None:
    """Z gate on all qubits."""


@hugr_op(logical_op(iceberg_ops.x_with_all_but_one_z_def))
@no_type_check
def x_with_all_but_one_z(block: Block[N], i: int) -> None:
    """X gate on the qubit with index `i`; Z on all others."""


@hugr_op(logical_op(iceberg_ops.z_with_all_but_one_x_def))
@no_type_check
def z_with_all_but_one_x(block: Block[N], i: int) -> None:
    """Z gate on the qubit with index `i`; X on all others."""


@hugr_op(logical_op(iceberg_ops.fan_out_def))
@no_type_check
def fan_out(block: Block[N], i: int) -> None:
    """Fan-out from the qubit with index `i` to all others."""


@hugr_op(logical_op(iceberg_ops.fan_in_def))
@no_type_check
def fan_in(block: Block[N], i: int) -> None:
    """Fan-in to the qubit with index `i` from all others."""


@hugr_op(logical_op(iceberg_ops.rx_def))
@no_type_check
def rx(block: Block[N], i: int, phase: float) -> None:
    """Rx rotation of `phase` radians on the qubit with index `i`."""


@guppy
@no_type_check
def ry(block: Block[N], i: int, phase: float) -> None:
    """Ry rotation on logical qubit `i`, using Rx and Rz with angles in radians."""
    rx(block, i, comptime(pi / 2))
    rz(block, i, phase)
    rx(block, i, comptime(-pi / 2))


@hugr_op(logical_op(iceberg_ops.rz_def))
@no_type_check
def rz(block: Block[N], i: int, phase: float) -> None:
    """Rz rotation of `phase` radians on the qubit with index `i`."""


@hugr_op(logical_op(iceberg_ops.pauli_exp_all_x_def))
@no_type_check
def pauli_exp_all_x(block: Block[N], phase: float) -> None:
    r"""Apply the logical all-X Pauli exponential.

    .. math::

        \exp(-i \theta X^{\otimes k} / 2)

    where :math:`\theta` is ``phase`` in radians and :math:`k` is the
    number of logical qubits in the block.
    """


@hugr_op(logical_op(iceberg_ops.pauli_exp_all_y_def))
@no_type_check
def pauli_exp_all_y(block: Block[N], phase: float) -> None:
    r"""Apply the logical all-Y Pauli exponential.

    .. math::

        \exp(-i \theta Y^{\otimes k} / 2)

    where :math:`\theta` is ``phase`` in radians and :math:`k` is the
    number of logical qubits in the block.
    """


@hugr_op(logical_op(iceberg_ops.pauli_exp_all_z_def))
@no_type_check
def pauli_exp_all_z(block: Block[N], phase: float) -> None:
    r"""Apply the logical all-Z Pauli exponential.

    .. math::

        \exp(-i \theta Z^{\otimes k} / 2)

    where :math:`\theta` is ``phase`` in radians and :math:`k` is the
    number of logical qubits in the block.
    """


@hugr_op(logical_op(iceberg_ops.pauli_exp_all_x_except_at_def))
@no_type_check
def pauli_exp_all_x_except_at(block: Block[N], i: int, phase: float) -> None:
    r"""Apply the Pauli exponential with I at ``i`` and X elsewhere.

    .. math::

        \exp(-i \theta (
            X^{\otimes i} \otimes I \otimes X^{\otimes(k-i-1)}
        ) / 2)

    where :math:`\theta` is ``phase`` in radians and :math:`k` is the
    number of logical qubits in the block.
    """


@hugr_op(logical_op(iceberg_ops.pauli_exp_all_z_except_at_def))
@no_type_check
def pauli_exp_all_z_except_at(block: Block[N], i: int, phase: float) -> None:
    r"""Apply the Pauli exponential with I at ``i`` and Z elsewhere.

    .. math::

        \exp(-i \theta (
            Z^{\otimes i} \otimes I \otimes Z^{\otimes(k-i-1)}
        ) / 2)

    where :math:`\theta` is ``phase`` in radians and :math:`k` is the
    number of logical qubits in the block.
    """


@hugr_op(logical_op(iceberg_ops.all_h_def))
@no_type_check
def all_h(block: Block[N]) -> None:
    """H gate on all qubits."""


@hugr_op(logical_op(iceberg_ops.xx_phase_def))
@no_type_check
def xx_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """XXPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.yy_phase_def))
@no_type_check
def yy_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """YYPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.zz_phase_def))
@no_type_check
def zz_phase(block: Block[N], i: int, j: int, phase: float) -> None:
    """ZZPhase rotation of `phase` radians on the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.cx_def))
@no_type_check
def cx(block: Block[N], i: int, j: int) -> None:
    """CX gate on the qubits with indices `i` (control) and `j` (target)."""


@hugr_op(logical_op(iceberg_ops.swap_def))
@no_type_check
def swap(block: Block[N], i: int, j: int) -> None:
    """Swap of the qubits with indices `i` and `j`."""


@hugr_op(logical_op(iceberg_ops.xx_phase_between_blocks_def))
@no_type_check
def xx_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """XXPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(logical_op(iceberg_ops.yy_phase_between_blocks_def))
@no_type_check
def yy_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """YYPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(logical_op(iceberg_ops.zz_phase_between_blocks_def))
@no_type_check
def zz_phase_between_blocks(
    block0: Block[N], block1: Block[N], i0: int, i1: int, phase: float
) -> None:
    """ZZPhase rotation of `phase` radians on the qubit with index `i0` in
    block `block0` and the qubit with index `i1` in block `block1`."""


@hugr_op(logical_op(iceberg_ops.cx_between_blocks_def))
@no_type_check
def cx_between_blocks(block0: Block[N], block1: Block[N], i0: int, i1: int) -> None:
    """CX gate on the qubit with index `i0` in block `block0` and the qubit with
    index `i1` in block `block1`."""


@hugr_op(logical_op(iceberg_ops.cx_transversal_def))
@no_type_check
def cx_transversal(block0: Block[N], block1: Block[N]) -> None:
    """CX gate applied transversally over `block0` and `block1`."""


@hugr_op(logical_op(iceberg_ops.free_def), effects=[Effect.ANY])
@no_type_check
def discard(block: Block[N] @ owned) -> None:
    """Free `block`."""


@hugr_op(logical_op(iceberg_ops.measure_syndrome_def))
@no_type_check
def measure_syndrome(block: Block[N]) -> tuple[Measurement, Measurement]:
    """Syndrome measurement."""


@hugr_op(logical_op(iceberg_ops.measure_all_def), effects=[Effect.ANY])
@no_type_check
def measure_all(block: Block[N] @ owned) -> LogicalMeasurement[N]:
    """Destructive measurement of all qubits in `block`."""


@hugr_op(logical_op(iceberg_ops.try_measure_one_x_def))
@no_type_check
def try_measure_one_x(block: Block[N], i: int) -> Option[Measurement]:
    """Fallible non-destructive measurement in the X basis of the qubit with
    index `i`."""


@hugr_op(logical_op(iceberg_ops.try_measure_one_z_def))
@no_type_check
def try_measure_one_z(block: Block[N], i: int) -> Option[Measurement]:
    """Fallible non-destructive measurement in the Z basis of the qubit with
    index `i`."""


@hugr_op(logical_op(iceberg_ops.try_alloc_dynq_def), effects=[Effect.ANY])
@no_type_check
def try_alloc_dynq() -> Option[Qubit]:
    """Fallible allocation of a qubit in the zero state."""


@hugr_op(logical_op(iceberg_ops.free_dynq_def), effects=[Effect.ANY])
@no_type_check
def free_dynq(qubit: Qubit @ owned) -> None:
    """Free `qubit`."""


@hugr_op(logical_op(iceberg_ops.x_dynq_def))
@no_type_check
def x_dynq(qubit: Qubit) -> None:
    """X gate."""


@hugr_op(logical_op(iceberg_ops.y_dynq_def))
@no_type_check
def y_dynq(qubit: Qubit) -> None:
    """Y gate."""


@hugr_op(logical_op(iceberg_ops.z_dynq_def))
@no_type_check
def z_dynq(qubit: Qubit) -> None:
    """Z gate."""


@hugr_op(logical_op(iceberg_ops.rx_dynq_def))
@no_type_check
def rx_dynq(qubit: Qubit, phase: float) -> None:
    """Rx rotation of `phase` radians."""


@guppy
@no_type_check
def ry_dynq(qubit: Qubit, phase: float) -> None:
    """Ry rotation of `phase` radians, implemented using Rx and Rz."""
    rx_dynq(qubit, comptime(pi / 2))
    rz_dynq(qubit, phase)
    rx_dynq(qubit, comptime(-pi / 2))


@hugr_op(logical_op(iceberg_ops.rz_dynq_def))
@no_type_check
def rz_dynq(qubit: Qubit, phase: float) -> None:
    """Rz rotation of `phase` radians."""


@hugr_op(logical_op(iceberg_ops.try_measure_x_dynq_def))
@no_type_check
def try_measure_x_dynq(qubit: Qubit) -> Option[Measurement]:
    """Fallible non-destructive measurement in the X basis."""


@hugr_op(logical_op(iceberg_ops.try_measure_z_dynq_def))
@no_type_check
def try_measure_z_dynq(qubit: Qubit) -> Option[Measurement]:
    """Fallible non-destructive measurement in the Z basis."""


@hugr_op(logical_op(iceberg_ops.xx_phase_dynq_def))
@no_type_check
def xx_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """XXPhase rotation of `phase` radians on two qubits."""


@hugr_op(logical_op(iceberg_ops.yy_phase_dynq_def))
@no_type_check
def yy_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """YYPhase rotation of `phase` radians on two qubits."""


@hugr_op(logical_op(iceberg_ops.zz_phase_dynq_def))
@no_type_check
def zz_phase_dynq(qubit0: Qubit, qubit1: Qubit, phase: float) -> None:
    """ZZPhase rotation of `phase` radians on two qubits."""


@hugr_op(logical_op(iceberg_ops.cx_dynq_def))
@no_type_check
def cx_dynq(qubit0: Qubit, qubit1: Qubit) -> None:
    """CX gate on `qubit0` (control) and `qubit1` (target)."""


@custom_function(_borrow_restore_compiler(iceberg_ops.borrow))
@no_type_check
def borrow(
    block: Block[N] @ owned, indices: array[int, M]
) -> (BorrowedBlock[N], array[Qubit, M]):
    """Extract dynamic logical qubits from a block."""


@custom_function(_borrow_restore_compiler(iceberg_ops.borrow_more))
@no_type_check
def borrow_more(block: BorrowedBlock[N], indices: array[int, M]) -> array[Qubit, M]:
    """Extract additional dynamic logical qubits from an already-borrowed block."""


@custom_function(_borrow_restore_compiler(iceberg_ops.restore_some))
@no_type_check
def restore_some(block: BorrowedBlock[N], qubits: array[Qubit, M] @ owned) -> None:
    """Restore some dynamic logical qubits to their originating block."""


@custom_function(_borrow_restore_compiler(iceberg_ops.restore))
@no_type_check
def restore(
    block: BorrowedBlock[N] @ owned, qubits: array[Qubit, M] @ owned
) -> Block[N]:
    """Restore all remaining dynamic logical qubits to their originating block."""
