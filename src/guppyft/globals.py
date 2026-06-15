import ast
from collections.abc import Callable
from typing import (
    Concatenate,
    ParamSpec,
    TypeVar,
    TypeVarTuple,
    overload,
    override,
)

from guppylang import guppy
from guppylang_internals.checker.errors.generic import ExpectedError, UnsupportedError
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
from guppylang_internals.engine import ENGINE
from guppylang_internals.error import GuppyTypeError
from guppylang_internals.nodes import GlobalCall, GlobalName
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
from hugr.tys import TypeBound
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
Ret = TypeVar("Ret")


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
        callback_expr, callback_func = ExprSynthesizer(self.ctx).synthesize(args[1])
        assert isinstance(callback_func, FunctionType)

        # Raise error if arg is borrowed
        for i, func_input in enumerate(callback_func.inputs):
            if InputFlags.Inout in func_input.flags:
                assert isinstance(callback_expr, GlobalName)
                callback_args: list[ast.arg] = ENGINE.get_parsed(  # type: ignore[union-attr]
                    callback_expr.def_id
                ).defined_at.args.args
                raise GuppyTypeError(
                    UnsupportedError(
                        callback_args[i],
                        "Borrowed args",
                        unsupported_in="callback input. Consider using `@owned`.",
                    )
                )

        # Check the number of input args provided matches callback function signature
        if len(args[2:]) != len(callback_func.inputs):
            expect_ty = ", ".join(str(i.ty) for i in callback_func.inputs)
            got_ty = ", ".join(
                str(ExprSynthesizer(self.ctx).synthesize(arg)[1]) for arg in args[2:]
            )
            raise GuppyTypeError(
                ExpectedError(
                    self.node,
                    f"input args ({expect_ty}) for callback func",
                    f"({got_ty}).",
                )
            )

        input_tys = [
            FuncInput(global_ty, InputFlags.NoFlags),
            FuncInput(callback_func, InputFlags.NoFlags),
        ]
        for arg, func_input in zip(args[2:], callback_func.inputs, strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_tys.append(FuncInput(arg_ty, func_input.flags))
            ExprChecker(self.ctx).check(arg, func_input.ty)

        match callback_func.output:
            case TupleType():
                output_ty = TupleType([global_ty, *callback_func.output.element_types])
            case NoneType():
                output_ty = global_ty
            case _:
                output_ty = TupleType([global_ty, callback_func.output])
        func_ty = FunctionType(
            inputs=input_tys,
            output=output_ty,
        )

        # Use default implementation from the expression checker
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


def with_op_instantiate(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        global_arg, func_ty, *input_args = concrete.input
        assert isinstance(func_ty, ht.FunctionType), (
            f"Expected a function, found {func_ty}."
        )

        return globals.with_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg.type_arg(),
                ht.ListArg(list[ht.TypeArg](a.type_arg() for a in input_args)),
                ht.ListArg(list[ht.TypeArg](a.type_arg() for a in func_ty.output)),
            ],
            concrete,
        )

    return op


def _get_map_output_args(func_output: Type, global_ty: Type) -> Type:
    # If output is global_ty, then outputs are None
    if func_output == global_ty:
        return NoneType()

    # Return then be TupleType
    assert isinstance(func_output, TupleType)
    # First arg must be global ty
    assert func_output.element_types[0] == global_ty, (
        f"{func_output.element_types[0]=}, {global_ty=}"
    )

    if len(func_output.element_types) == 2:
        # If the only return is a Tuple, it must be repacked in a Tuple
        # to match signatures between Guppy and HUGR.
        if isinstance(func_output.element_types[1], TupleType):
            return TupleType([func_output.element_types[1]])
        else:
            return func_output.element_types[1]
    elif len(func_output.element_types) > 2:
        return TupleType(func_output.element_types[1:])
    else:
        return NoneType()


@overload
def with_global[G, **P, *R](
    initial_state: G,
    callback_func: Callable[P, tuple[*R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[G, *R]: ...
@overload
def with_global[G, **P, Ret](
    initial_state: G,
    callback_func: Callable[P, Ret],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[G, Ret]: ...
@custom_function(  # type: ignore[misc, arg-type]
    checker=GlobalWithChecker(),
    compiler=GlobalOpCompiler(with_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def with_global[G, **P, *R, Ret](  # type: ignore[empty-body]
    initial_state: G,
    callback_func: Callable[P, tuple[*R] | Ret],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[G, *R] | tuple[G, Ret]: ...


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
                global_ty.type_arg(),
                ht.ListArg(list[ht.TypeArg](a.type_arg() for a in input_args)),
                ht.ListArg(list[ht.TypeArg](a.type_arg() for a in func_ty.output[1:])),
            ],
            concrete,
        )

    return op


class GlobalMapChecker(CustomCallChecker):
    @override
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        # First arg is the callback function
        callback_expr, callback_func = ExprSynthesizer(self.ctx).synthesize(args[0])
        assert isinstance(callback_func, FunctionType)
        global_ty = callback_func.inputs[0]
        # TODO This is not a fundamental limitation but there is a mismatch between how
        #  Guppy and HUGR unpack tuples that needs to be fixed.
        if isinstance(global_ty.ty, TupleType):
            raise TypeError("Global type cannot be tuple.")
        # Global type must be owned if linear
        if (
            global_ty.ty.hugr_bound == TypeBound.Linear
            and InputFlags.Owned not in global_ty.flags
        ):
            assert isinstance(callback_expr, GlobalName)
            callback_args: list[ast.arg] = ENGINE.get_parsed(  # type: ignore[union-attr]
                callback_expr.def_id
            ).defined_at.args.args
            raise GuppyTypeError(
                ExpectedError(
                    callback_args[0],
                    "global type to be owned. Linear global arg must be "
                    "decorated with `@ owned`.",
                )
            )

        # Raise error if input arg is borrowed/inout
        for i in callback_func.inputs:
            if InputFlags.Inout in i.flags:
                # TODO turn this into a nice Guppy compiler error
                raise ValueError(
                    "Input args cannot be borrowed. Consider using `@owned`."
                )

        input_args = [FuncInput(callback_func, InputFlags.NoFlags)]
        for arg, func_input in zip(args[1:], callback_func.inputs[1:], strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_args.append(FuncInput(arg_ty, func_input.flags))

        # callback_func output is [global state, *out_args]
        output_args = _get_map_output_args(callback_func.output, global_ty.ty)

        func_ty = FunctionType(
            inputs=input_args,
            output=output_args,
        )

        # Use default implementation from the expression checker
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


@overload
def map_global[G, **P](
    callback_func: Callable[Concatenate[G, P], G],
    *args: P.args,
    **kwargs: P.kwargs,
) -> None: ...
@overload
def map_global[G, **P, *R](
    callback_func: Callable[Concatenate[G, P], tuple[G, *R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[*R]: ...
@custom_function(  # type: ignore[misc, arg-type]
    checker=GlobalMapChecker(),
    compiler=GlobalOpCompiler(map_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def map_global[G, **P, *R](  # type: ignore[empty-body]
    callback_func: Callable[Concatenate[G, P], G | tuple[G, *R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[*R]: ...
