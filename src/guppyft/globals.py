"""Methods for handling global state."""

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

from guppylang_internals.checker.errors.generic import ExpectedError
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
    InputFlagDefaultMode,
)
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.error import GuppyTypeError
from guppylang_internals.nodes import GlobalCall
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import (
    FuncInput,
    FunctionDefType,
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

from guppyft._errors import (
    CallbackFuncDefinedHere,
    CallbackFuncParametersError,
    CallbackInputParamError,
    CallbackOutputArgError,
    CallbackOutputGlobalTupleError,
    CallbackUsedHereNote,
    ConsiderOwnedHelper,
    MapCallbackSignatureHelper,
    WithCallbackSignatureHelper,
    get_callback_func_ast,
)

# Mark ops as having side effects to add order edges in the HUGR
# when calls return None.
# https://github.com/Quantinuum/guppylang/issues/1698
if "tket.globals.with" not in EXTENSION_OPS_WITH_SIDE_EFFECTS:
    EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.with")
if "tket.globals.map" not in EXTENSION_OPS_WITH_SIDE_EFFECTS:
    EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.map")

GLOBAL_VAR_NAME = "guppy_ft_global"

G = TypeVar("G")
P = ParamSpec("P")
R = TypeVarTuple("R")
Ret = TypeVar("Ret")


class _GlobalOpCompiler(CustomInoutCallCompiler):
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


class _GlobalWithChecker(CustomCallChecker):
    # `with_global` has variadic args, and its callback params can never be
    # borrowed (enforced below), so all linear input args are consumed/owned.
    input_flag_mode = InputFlagDefaultMode.OWNED

    @override
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        _, global_ty = ExprSynthesizer(self.ctx).synthesize(args[0])
        callback_expr, callback_def = ExprSynthesizer(self.ctx).synthesize(args[1])
        if not isinstance(callback_def, FunctionDefType):
            err = ExpectedError(callback_expr, "FunctionType", str(callback_def))
            err.add_sub_diagnostic(WithCallbackSignatureHelper(None))
            raise GuppyTypeError(err)
        callback_func = callback_def.sig

        # Raise error if arg is borrowed
        for i, func_input in enumerate(callback_func.inputs):
            if InputFlags.Inout in func_input.flags:
                err = CallbackInputParamError(
                    callback_expr,
                    i,
                    (
                        "Parameters in callback functions used in global operations"
                        " cannot be borrowed."
                    ),
                )
                err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
                err.add_sub_diagnostic(ConsiderOwnedHelper(None))
                raise GuppyTypeError(err)

        # Check the number of input args provided matches callback function signature
        if len(args[2:]) != len(callback_func.inputs):
            got_func_inputs = [
                ExprSynthesizer(self.ctx).synthesize(arg)[1] for arg in args[2:]
            ]
            err = CallbackFuncParametersError(
                self.node,
                callback_func.inputs,
                got_func_inputs,
            )
            callback_def = get_callback_func_ast(callback_expr)
            err.add_sub_diagnostic(CallbackFuncDefinedHere(callback_def))
            err.add_sub_diagnostic(WithCallbackSignatureHelper(None))
            raise GuppyTypeError(err)

        # with op signature is (global, func[*in, *out], *in) -> (global, *out)
        input_tys = [
            FuncInput(global_ty, InputFlags.NoFlags),
            FuncInput(callback_func, InputFlags.NoFlags),
        ]
        for arg, func_input in zip(args[2:], callback_func.inputs, strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_tys.append(FuncInput(arg_ty, func_input.flags))
            try:
                ExprChecker(self.ctx).check(arg, func_input.ty)
            except GuppyTypeError as err:
                callback_def = get_callback_func_ast(callback_expr)
                err.error.add_sub_diagnostic(CallbackFuncDefinedHere(callback_def))
                err.error.add_sub_diagnostic(WithCallbackSignatureHelper(None))
                raise

        match callback_func.output:
            case TupleType():
                output_ty = TupleType([global_ty, *callback_func.output.element_types])
            case NoneType():
                if isinstance(global_ty, TupleType):
                    # If global type is a tuple, then it must be wrapped in another
                    # tuple to match HUGR op signature
                    output_ty = TupleType([global_ty])
                else:
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


def _with_op_instantiate(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        global_arg, func_ty, *input_args = concrete.input
        assert isinstance(func_ty, ht.FunctionType)

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
    checker=_GlobalWithChecker(),
    compiler=_GlobalOpCompiler(_with_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def with_global[G, **P, *R, Ret](  # type: ignore[empty-body]
    initial_state: G,
    callback_func: Callable[P, tuple[*R] | Ret],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[G, *R] | tuple[G, Ret]: ...


def _map_op_instantiate(
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


class _GlobalMapChecker(CustomCallChecker):
    # `map_global` has variadic args, and its callback params can never be
    # borrowed (enforced below), so all linear input args are consumed/owned.
    input_flag_mode = InputFlagDefaultMode.OWNED

    @override
    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        # First arg is the callback function
        callback_expr, callback_def = ExprSynthesizer(self.ctx).synthesize(args[0])
        match callback_def:
            case FunctionType():
                callback_func = callback_def
            case FunctionDefType():
                callback_func = callback_def.sig
            case _:
                err = ExpectedError(callback_expr, "FunctionType", str(callback_def))
                err.add_sub_diagnostic(MapCallbackSignatureHelper(None))
                raise GuppyTypeError(err)

        try:
            global_arg = callback_func.inputs[0]
            global_ty = global_arg.ty
        except IndexError as e:
            err = CallbackInputParamError(
                callback_expr,
                None,
                "Callback function used in global map missing global input parameter",
            )
            err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
            raise GuppyTypeError(err) from e
        # Global type must be owned if linear
        if (
            global_ty.hugr_bound == TypeBound.Linear
            and InputFlags.Owned not in global_arg.flags
        ):
            err = CallbackInputParamError(
                callback_expr,
                0,
                "First argument to callback function in global map is the "
                "global variable and cannot be borrowed.",
            )
            err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
            err.add_sub_diagnostic(ConsiderOwnedHelper(None))
            raise GuppyTypeError(err)

        # Raise error if input arg is borrowed/inout
        for i, input_arg in enumerate(callback_func.inputs):
            if InputFlags.Inout in input_arg.flags:
                err = CallbackInputParamError(
                    callback_expr,
                    i,
                    (
                        "Parameters in callback functions used in global operations"
                        " cannot be borrowed."
                    ),
                )
                err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
                err.add_sub_diagnostic(ConsiderOwnedHelper(None))
                raise GuppyTypeError(err)

        # Check the number of input args provided matches callback function signature
        if len(args[1:]) != len(callback_func.inputs[1:]):
            got_func_inputs = [
                ExprSynthesizer(self.ctx).synthesize(arg)[1] for arg in args[1:]
            ]
            err = CallbackFuncParametersError(
                self.node,
                callback_func.inputs[1:],
                got_func_inputs,
            )
            callback_def = get_callback_func_ast(callback_expr)
            err.add_sub_diagnostic(CallbackFuncDefinedHere(callback_def))
            err.add_sub_diagnostic(MapCallbackSignatureHelper(None))
            raise GuppyTypeError(err)

        input_args = [FuncInput(callback_func, InputFlags.NoFlags)]
        for arg, func_input in zip(args[1:], callback_func.inputs[1:], strict=True):
            _, arg_ty = ExprSynthesizer(self.ctx).synthesize(arg)
            input_args.append(FuncInput(arg_ty, func_input.flags))
            try:
                ExprChecker(self.ctx).check(arg, func_input.ty)
            except GuppyTypeError as err:
                callback_def = get_callback_func_ast(callback_expr)
                err.error.add_sub_diagnostic(CallbackFuncDefinedHere(callback_def))
                err.error.add_sub_diagnostic(MapCallbackSignatureHelper(None))
                raise

        # callback_func output is [global state, *out_args]
        callback_output = callback_func.output
        match callback_output:
            case TupleType():
                # If callback_output and global type are equal, then the global type
                # is a tuple and is the only return from the callback. The Guppy
                # compiler unpacks tuple return types, while HUGR ops do not. To
                # avoid this, the callback output must be packed into a tuple
                # i.e. tuple[tuple[...]].
                if global_ty == callback_output:
                    assert isinstance(global_ty, TupleType)
                    callback_def = get_callback_func_ast(callback_expr)
                    err = CallbackOutputGlobalTupleError(
                        callback_def.returns,  # type: ignore[union-attr]
                        global_ty,
                    )
                    err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
                    raise GuppyTypeError(err)

                # First output must be global ty
                if callback_output.element_types[0] != global_arg.ty:
                    callback_def = get_callback_func_ast(callback_expr)
                    err = CallbackOutputArgError(callback_def.returns, global_arg.ty)  # type: ignore[union-attr]
                    err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
                    err.add_sub_diagnostic(MapCallbackSignatureHelper(None))
                    raise GuppyTypeError(err)
                if len(callback_output.element_types) == 2:
                    # If the only return is a tuple, it must be repacked in a tuple
                    # to match signatures between Guppy and HUGR.
                    if isinstance(callback_output.element_types[1], TupleType):
                        output_args = TupleType([callback_output.element_types[1]])
                    else:
                        output_args = callback_output.element_types[1]
                else:
                    output_args = TupleType(callback_output.element_types[1:])
            case _:
                if callback_output != global_arg.ty:
                    callback_def = get_callback_func_ast(callback_expr)
                    err = CallbackOutputArgError(callback_def.returns, global_arg.ty)  # type: ignore[union-attr]
                    err.add_sub_diagnostic(CallbackUsedHereNote(callback_expr))
                    err.add_sub_diagnostic(MapCallbackSignatureHelper(None))
                    raise GuppyTypeError(err)
                output_args = NoneType()

        func_ty = FunctionType(
            inputs=input_args,
            output=output_args,
        )

        # Use default implementation from the expression checker
        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


@overload
def map_global[G, **P, *R](  # type: ignore[overload-overlap]
    callback_func: Callable[Concatenate[G, P], tuple[G, *R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[*R]: ...
@overload
def map_global[G, **P](
    callback_func: Callable[Concatenate[G, P], G],
    *args: P.args,
    **kwargs: P.kwargs,
) -> None: ...
@custom_function(  # type: ignore[misc, arg-type]
    checker=_GlobalMapChecker(),
    compiler=_GlobalOpCompiler(_map_op_instantiate(GLOBAL_VAR_NAME)),
    higher_order_value=False,
)
def map_global[G, **P, *R](  # type: ignore[empty-body]
    callback_func: Callable[Concatenate[G, P], G | tuple[G, *R]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> tuple[*R]: ...
