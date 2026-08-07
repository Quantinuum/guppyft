import ast
from collections.abc import Callable, Sequence
from typing import Generic, no_type_check, override

import hugr.tys as ht
from guppylang import guppy
from guppylang_internals.checker.expr_checker import ExprSynthesizer, synthesize_call
from guppylang_internals.compiler.core import CompilerContext
from guppylang_internals.decorator import custom_function, custom_type
from guppylang_internals.definition.custom import (
    CustomCallChecker,
    CustomInoutCallCompiler,
)
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.nodes import GlobalCall
from guppylang_internals.tys.arg import Argument, ConstArg
from guppylang_internals.tys.builtin import bool_type
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.const import ConstValue
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import (
    FuncInput,
    FunctionType,
    InputFlags,
    NumericType,
    OpaqueType,
    TupleType,
    Type,
)
from hugr import Wire
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


class _DecodeChecker(CustomCallChecker):
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        _, self_ty = ExprSynthesizer(self.ctx).synthesize(args[0])
        assert isinstance(self_ty, OpaqueType), type(self_ty)
        [k_arg] = self_ty.args
        assert isinstance(k_arg, ConstArg)
        assert isinstance(k_arg.const, ConstValue)
        n = k_arg.const.value

        out_ty = bool_type() if n == 1 else TupleType([bool_type()] * n)

        func_ty = FunctionType(
            inputs=[FuncInput(self_ty, InputFlags.NoFlags)],
            output=out_ty,
        )
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


class _DecodeCompiler(CustomInoutCallCompiler):
    op: Callable[[ht.FunctionType, Inst, CompilerContext], DataflowOp]

    def __init__(
        self, op: Callable[[ht.FunctionType, Inst, CompilerContext], DataflowOp]
    ) -> None:
        self.op = op

    @override
    def compile_with_inouts(self, args: list[Wire]) -> CallReturnWires:
        op = self.op(self.ty, self.type_args, self.ctx)
        node = self.builder.add_op(op, *args)
        num_returns = len(self.ty.output)
        return CallReturnWires(
            regular_returns=list(node[:num_returns]),
            inout_returns=list(node[num_returns:]),
        )


N = guppy.nat_var("N")


@custom_type(
    _std_ty("logical_measurement"),
    copyable=True,
    droppable=True,
    params=[ConstParam(1, "k", NumericType(NumericType.Kind.Nat))],
)
class LogicalMeasurement(Generic[N]):  # type: ignore[misc]
    @custom_function(
        checker=_DecodeChecker(),
        compiler=_DecodeCompiler(_std_op("decode")),
        higher_order_value=False,
    )
    @no_type_check
    def decode(self: "LogicalMeasurement[N]") -> None:
        """Decode logical measurement"""
