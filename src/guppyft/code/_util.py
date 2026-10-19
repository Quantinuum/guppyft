"""Utilities for defining logical-code HUGR operations."""

from collections.abc import Callable

import tket_exts
from guppylang_internals.compiler.builder import pure
from guppylang_internals.compiler.builder.ops import unpack_tuple
from guppylang_internals.definition.custom import CustomInoutCallCompiler
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.std._internal.compiler.array import array_new, unpack_array
from guppylang_internals.std._internal.compiler.quantum import from_halfturns_unchecked
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import Wire
from hugr import tys as ht
from hugr.ext import OpDef
from hugr.ops import DataflowOp, ExtOp
from hugr.std.float import FLOAT_T
from hugr.std.int import int_t


def logical_op(
    op_def: OpDef,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    """Utility method to create HUGR logical ops.

    Args:
        op_def: The extension op definition to create a logical op from.

    Returns:
        A function that takes an instantiation of the type arguments and returns
        a concrete HUGR op.
    """

    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(op_def, ty, [arg.to_hugr(ctx) for arg in inst])

    return op


class RotationCompiler(CustomInoutCallCompiler):
    op_def: OpDef

    def __init__(self, op_def: OpDef):
        self.op_def = op_def

    def compile_with_inouts(self, args: list[Wire]) -> CallReturnWires:
        [*qs, angle] = args
        [halfturns] = self.builder.add_op(unpack_tuple([FLOAT_T]), angle)
        [rotation] = self.builder.add_op(from_halfturns_unchecked(), halfturns)

        if not qs:
            func_ty = ht.FunctionType([tket_exts.rotation.rotation], [])
        else:
            qubit_ty = self.ty.input[0]
            func_ty = ht.FunctionType(
                [qubit_ty for _ in qs] + [tket_exts.rotation.rotation], self.ty.output
            )

        qs = self.builder.add_op(
            pure(logical_op(self.op_def)(func_ty, (), self.ctx)),
            *qs,
            rotation,
        )

        return CallReturnWires(regular_returns=[], inout_returns=list(qs))


class BorrowRestoreCompiler(CustomInoutCallCompiler):
    """Adapt array-based Guppy borrowing to variadic logical HUGR operations.

    The operation factory receives the array length and the concrete owning
    block type. It must instantiate one of `borrow`, `borrow_more`, `restore_some`,
    or `restore` with its native signature and static arguments. This keeps code
    parameters and their ordering outside the shared compiler, supporting both
    fixed-size and parameterized code blocks.

    Native operations return the owning block first. Guppy instead puts regular
    returns before inout arguments, so borrow_more requires reordered outputs.
    Borrowed index arrays are rebuilt to preserve Guppy's inout contract.
    """

    def __init__(
        self,
        instantiate_op: Callable[[int, ht.ExtType], ExtOp],
        qubit_type: ht.Type,
    ) -> None:
        self.instantiate_op = instantiate_op
        self.qubit_type = qubit_type

    def compile_with_inouts(self, args: list[Wire]) -> CallReturnWires:
        """Unpack arrays, emit a native op, and reconstruct Guppy returns."""
        owner, array = args
        owner_type = self.builder.get_wire_type(owner)
        assert isinstance(owner_type, ht.ExtType)
        elements = unpack_array(self.builder, array)
        m = len(elements)
        op = self.instantiate_op(m, owner_type)
        name = op.op_def().name
        if name not in {"borrow", "borrow_more", "restore_some", "restore"}:
            raise ValueError(f"Unsupported borrow/restore operation: {name}")
        outputs: list[Wire] = list(self.builder.add_op(pure(op), owner, *elements))
        if name in {"borrow", "borrow_more"}:
            owner, *qubits = outputs
            qubit_array = self.builder.add_op(array_new(self.qubit_type, m), *qubits)
            indices = self.builder.add_op(array_new(int_t(6), m), *elements)
            if name == "borrow":
                return CallReturnWires([owner, qubit_array], [indices])
            return CallReturnWires([qubit_array], [owner, indices])
        if name == "restore_some":
            return CallReturnWires([], outputs)
        return CallReturnWires(outputs, [])
