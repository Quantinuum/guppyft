"""Standard types and operations shared between QEC architectures."""

from collections.abc import Callable, Sequence
from typing import Generic, no_type_check

import hugr.tys as ht
from guppylang import guppy
from guppylang.std.builtins import array
from guppylang_internals.compiler.core import CompilerContext
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys.arg import Argument, ConstArg
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import NumericType
from hugr.ops import DataflowOp, ExtOp

from guppyft.extensions import std_ops, std_types

OPS_EXTN = std_ops()
TYPES_EXTN = std_types()


def _std_ty(
    ty_name: str,
) -> Callable[[Sequence[Argument], CompilerContext], ht.Type]:
    def ty(args: Sequence[Argument], ctx: ToHugrContext) -> ht.Type:
        [k_arg] = args
        assert isinstance(k_arg, ConstArg)
        return ht.ExtType(TYPES_EXTN.get_type(ty_name), [k_arg.to_hugr(ctx)])

    return ty


def _std_op(
    op_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(OPS_EXTN.get_op(op_name), ty, [arg.to_hugr(ctx) for arg in inst])

    return op


N = guppy.nat_var("N")


@custom_type(
    _std_ty("logical_measurement"),
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


@hugr_op(_std_op("decode"))
@no_type_check
def decode(meas: LogicalMeasurement[N]) -> array[bool, N]:
    """Decode logical measurement"""
