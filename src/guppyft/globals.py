from collections.abc import Callable
from typing import cast, no_type_check

from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang_internals.compiler.core import (
    EXTENSION_OPS_WITH_SIDE_EFFECTS,
)
from guppylang_internals.decorator import hugr_op
from guppylang_internals.tys.arg import Argument, TypeArg
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import NoneType, TupleType
from hugr import ops
from hugr import tys as ht
from tket_exts import globals

T = guppy.type_var("T", copyable=False, droppable=False)

IN = guppy.type_var("IN")
L_IN = guppy.type_var("L_IN", copyable=False, droppable=False)
OUT = guppy.type_var("OUT")

# Mark ops as having side effects to add order edges in the HUGR
# when calls return None.
# https://github.com/Quantinuum/guppylang/issues/1698
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.with")
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.map")


def with_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        global_arg = cast("ht.TypeTypeArg", args[0].to_hugr(ctx))

        if global_arg.ty.type_bound() != ht.TypeBound.Linear:
            raise TypeError(f"Global arg must be linear. Found {global_arg.ty}.")

        return globals.with_def.instantiate(
            [ht.StringArg(var_name), global_arg, ht.ListArg([]), ht.ListArg([])],
            concrete,
        )

    return op


@hugr_op(with_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def with_global_state(func: Callable[[], None], new_value: T @ owned) -> T: ...


def _unpack_tuple_arg(arg: Argument, ctx: ToHugrContext) -> list[ht.TypeArg]:
    match arg:
        case TypeArg(ty=gty):
            match gty:
                case TupleType(args=elems):
                    return [ty.to_hugr(ctx) for ty in elems]
                case NoneType():
                    return []
                case _:
                    return [arg.to_hugr(ctx)]
        case _:
            return [arg.to_hugr(ctx)]


def _map_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        if len(args) == 2:
            input_args = ht.ListArg([])
            global_arg = args[0].to_hugr(ctx)
            # There is a mismatch in function signatures between the Guppy compiler
            # and the HUGR Op instantiation. The Guppy compile unpacks tuples at
            # the output of functions while HUGR does not. It is necessary for us
            # to manually unpack the tuple type here for the signatures to match.
            output_args = ht.ListArg(_unpack_tuple_arg(args[1], ctx))
        else:
            input_args = ht.ListArg([args[0].to_hugr(ctx)])
            global_arg = args[1].to_hugr(ctx)

            input_ty_arg = args[0]
            assert isinstance(input_ty_arg, TypeArg)
            if input_ty_arg.ty.copyable:
                output_args = ht.ListArg(_unpack_tuple_arg(args[2], ctx))
            else:
                output_args = ht.ListArg(
                    [*_unpack_tuple_arg(args[2], ctx), args[0].to_hugr(ctx)]
                )

        return globals.map_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg,
                input_args,
                output_args,
            ],
            concrete,
        )

    return op


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_state_input(func: Callable[[IN, T], OUT], inputs: IN) -> OUT: ...


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_state_linear_input(
    func: Callable[[L_IN, T], OUT], inputs: L_IN
) -> OUT: ...


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_state_no_input(func: Callable[[T], OUT]) -> OUT: ...


@guppy.overload(
    _map_global_state_input, _map_global_state_linear_input, _map_global_state_no_input
)
def map_global_state(state: T, args: IN | None = None) -> OUT: ...  # type: ignore[valid-type]
