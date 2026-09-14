"""Utilities for defining logical-code HUGR operations."""

from collections.abc import Callable

from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import tys as ht
from hugr.ext import Extension
from hugr.ops import DataflowOp, ExtOp


def _logical_op(
    op_name: str,
    extension: Extension,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    """Utility method to create HUGR logical ops.

    args:
        op_name: The name of the operation.
        ext: The extension of the operation.

    Returns:
        A function that takes an instantiation of the type arguments and returns
        a concrete HUGR op.
    """

    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(
            extension.get_op(op_name),
            ty,
            [arg.to_hugr(ctx) for arg in inst],
        )

    return op
