import ast
from collections.abc import Callable
from typing import (
    Any,
    Concatenate,
    ParamSpec,
    TypeVar,
    TypeVarTuple,
    override,
)

from guppylang import guppy
from guppylang_internals.checker.expr_checker import (
    ExprChecker,
    ExprSynthesizer,
    synthesize_call,
)
from guppylang_internals.compiler.core import (
    EXTENSION_OPS_WITH_SIDE_EFFECTS,
    CompilerContext,
)
from guppylang_internals.decorator import custom_function
from guppylang_internals.definition.custom import (
    CustomCallChecker,
    CustomInoutCallCompiler,
)
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.nodes import GlobalCall
from guppylang_internals.tys.builtin import string_type
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import (
    FuncInput,
    FunctionType,
    InputFlags,
    NoneType,
    TupleType,
    Type,
)
from hugr import Wire, ops
from hugr import tys as ht
from hugr.tys import TypeArg, TypeBound
from tket_exts import globals

State = guppy.type_var("State")
State_Linear = guppy.type_var("State_Linear", copyable=False, droppable=False)
In = guppy.type_var("In")
In_Linear = guppy.type_var("In_Linear", copyable=False, droppable=False)
Out = guppy.type_var("OUT", copyable=False, droppable=False)

# Mark ops as having side effects to add order edges in the HUGR
# when calls return None.
# https://github.com/Quantinuum/guppylang/issues/1698
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.with")
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.map")

GLOBAL_VAR_NAME = "guppy_ft_global"

G = TypeVar("G")
P = ParamSpec("P")
R = TypeVarTuple("R")


class GlobalOpCompiler(CustomInoutCallCompiler):
    op: Callable[[ht.FunctionType, Inst, CompilerContext], ops.DataflowOp]

    def __init__(
        self, op: Callable[[ht.FunctionType, Inst, CompilerContext], ops.DataflowOp]
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


class GlobalWithChecker(CustomCallChecker):
    @override
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        _, global_ty = ExprSynthesizer(self.ctx).synthesize(args[0])

        _, with_func_ty = ExprSynthesizer(self.ctx).synthesize(args[1])
        assert isinstance(with_func_ty, FunctionType)

        # TODO use ExprChecker to turn this into a nice Guppy compiler error
        # Raise error if arg is borrowed
        for i in with_func_ty.inputs:
            if InputFlags.Inout in i.flags:
                raise ValueError(
                    "Input args cannot be borrowed. Consider using `@owned`."
                )

        input_args = [
            FuncInput(global_ty, InputFlags.NoFlags),
            FuncInput(with_func_ty, InputFlags.NoFlags),
        ]
        # Check the number of input args provided matches
        assert len(args[2:]) == len(with_func_ty.inputs)
        for arg, func_input in zip(args[2:], with_func_ty.inputs, strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_args.append(FuncInput(arg_ty, func_input.flags))
            ExprChecker(self.ctx).check(arg, func_input.ty)

        match with_func_ty.output:
            case TupleType():
                output_args = TupleType([global_ty, *with_func_ty.output.element_types])
            case NoneType():
                output_args = global_ty
            case _:
                output_args = TupleType([global_ty, with_func_ty.output])
        func_ty = FunctionType(
            inputs=input_args,
            output=output_args,
        )

        # Use default implementation from the expression checker
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


def with_op_instantiate(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        global_arg, func_ty, *input_args = concrete.input

        return globals.with_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg,
                ht.ListArg(input_args),
                ht.ListArg(func_ty.output),
            ],
            concrete,
        )

    return op


@custom_function(
    checker=GlobalWithChecker(),
    compiler=GlobalOpCompiler(with_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def with_global[G, **P, *R](
    initial_state: G,
    func: Callable[P, *R],
    *args: P.args,
) -> tuple[G, *R]: ...


def map_op_instantiate(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        func_ty, *input_args = concrete.input
        assert isinstance(func_ty, ht.FunctionType), (
            f"Expected a function, found {func_ty}."
        )
        global_ty = func_ty.input[0]

        return globals.map_def.instantiate(
            [
                ht.StringArg(var_name),
                global_ty,
                ht.ListArg(list[ht.TypeArg](input_args)),
                ht.ListArg(list[ht.TypeArg](func_ty.output[1:])),
            ],
            concrete,
        )

    return op


class GlobalMapChecker(CustomCallChecker):
    @override
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        # First arg is function to be mapped
        _, map_func_ty = ExprSynthesizer(self.ctx).synthesize(args[0])
        assert isinstance(map_func_ty, FunctionType)
        # Global type must be owned if linear
        global_ty = map_func_ty.inputs[0]
        if global_ty.ty.hugr_bound == TypeBound.Linear:
            assert InputFlags.Owned in global_ty.flags

        # Raise error if input arg is borrowed/inout
        for i in map_func_ty.inputs:
            if InputFlags.Inout in i.flags:
                # TODO turn this into a nice Guppy compiler error
                raise ValueError(
                    "Input args cannot be borrowed. Consider using `@owned`."
                )

        input_args = [FuncInput(map_func_ty, InputFlags.NoFlags)]
        for arg, func_input in zip(args[1:], map_func_ty.inputs[1:], strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_args.append(FuncInput(arg_ty, func_input.flags))

        # mapped func output is [global state, *out_args]
        func_out = map_func_ty.output
        match func_out:
            case TupleType():
                # For multiple outputs, global_ty must be first
                # assert func_out.element_types[0] == global_ty, (
                #     f"{func_out.element_types[0]=}, {global_ty=}"
                # )
                output_args = (
                    TupleType(func_out.element_types[1:])
                    if len(func_out.element_types) > 2
                    else func_out.element_types[1]
                )
            case _:
                # For single return, it must be global_ty
                assert func_out == global_ty.ty
                output_args = NoneType()

        func_ty = FunctionType(
            inputs=input_args,
            output=output_args,
        )

        # Use default implementation from the expression checker
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


@custom_function(
    checker=GlobalMapChecker(),
    compiler=GlobalOpCompiler(map_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def map_global[G, **P, *R](
    func: Callable[Concatenate[G, P], tuple[G, *R] | G],
    *args: P.args,
) -> tuple[*R]: ...
