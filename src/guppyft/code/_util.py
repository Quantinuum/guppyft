"""Utilities for defining logical-code HUGR operations."""

from collections.abc import Callable

import tket_exts
from guppylang_internals.compiler.builder import pure
from guppylang_internals.compiler.builder.ops import unpack_tuple
from guppylang_internals.definition.custom import CustomInoutCallCompiler
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.std._internal.compiler.quantum import from_halfturns_unchecked
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import Wire
from hugr import tys as ht
from hugr.ext import OpDef
from hugr.ops import DataflowOp, ExtOp
from hugr.std.float import FLOAT_T


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
