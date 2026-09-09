from collections.abc import Callable, Sequence
from typing import Generic, no_type_check

import hugr.tys as ht
from guppylang import guppy
from guppylang.std.builtins import array
from guppylang_internals.compiler.core import CompilerContext
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys.arg import Argument
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import NumericType
from hugr.ext import OpDef, TypeDef
from hugr.ops import DataflowOp, ExtOp

from guppyft.extensions import std_ops, std_types


def _instantiator_for_ty(
    ty_def: TypeDef,
) -> Callable[[Sequence[Argument], CompilerContext], ht.Type]:
    def ty(args: Sequence[Argument], ctx: ToHugrContext) -> ht.Type:
        return ht.ExtType(ty_def, [arg.to_hugr(ctx) for arg in args])

    return ty


def _instantiator_for_op(
    op_def: OpDef,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(op_def, ty, [arg.to_hugr(ctx) for arg in inst])

    return op


N = guppy.nat_var("N")


@custom_type(
    _instantiator_for_ty(std_types.logical_measurement_def),
    copyable=True,
    droppable=True,
    params=[ConstParam(1, "k", NumericType(NumericType.Kind.Nat))],
)
class LogicalMeasurement(Generic[N]):  # type: ignore[misc]
    @guppy
    @no_type_check
    def decode(self: "LogicalMeasurement[N]") -> array[bool, N]:
        """Decode logical measurement"""
        return decode(self)


@hugr_op(_instantiator_for_op(std_ops.decode_def))
@no_type_check
def decode(meas: LogicalMeasurement[N]) -> array[bool, N]:
    """Decode logical measurement"""
