from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang.std.option import Option
from guppylang_internals.decorator import hugr_op
from guppylang_internals.tys.arg import Argument
from guppylang_internals.tys.arg import TypeArg as GuppyTypeArg
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from guppylang_internals.tys.ty import NoneType, TupleType
from hugr import ops
from hugr import tys as ht
from hugr.tys import ListArg, TypeArg
from tket_exts import globals

GLOBALS_EXTENSION = globals()


# TODO MOVE TO TKET
def swap_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    op_def = GLOBALS_EXTENSION.get_op("swap")

    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        return op_def.instantiate(
            [ht.StringArg(var_name)] + [arg.to_hugr(ctx) for arg in args], concrete
        )

    return op


T = guppy.type_var("T", copyable=False, droppable=False)

IN = guppy.type_var("IN")
OUT = guppy.type_var("OUT")


# TODO MOVE INTO CODES (maybe a default renaming)
@hugr_op(swap_op_for_global_var("GLOBAL_STATE"))
@no_type_check
def swap_global_state_generic(new_value: Option[T] @ owned) -> Option[T]: ...


def with_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    op_def = GLOBALS_EXTENSION.get_op("with")

    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        return op_def.instantiate(
            [ht.StringArg(var_name)]
            + [arg.to_hugr(ctx) for arg in args]
            + [ListArg([])]
            + [ListArg([])],
            concrete,
        )

    return op


@hugr_op(with_op_for_global_var("GLOBAL_STATE"))
@no_type_check
def with_global_state_generic(new_value: T @ owned, func: Callable[[], None]) -> T: ...


def _unpack_tuple_arg(arg: Argument, ctx: ToHugrContext) -> list[TypeArg]:
    match arg:
        case GuppyTypeArg(ty=gty):
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
        op_def = GLOBALS_EXTENSION.get_op("map")
        return op_def.instantiate(
            [
                ht.StringArg(var_name),
                args[0].to_hugr(ctx),
                ListArg([args[1].to_hugr(ctx)]),
                ListArg(_unpack_tuple_arg(args[2], ctx)),  # TODO COMMENT LOTS
            ],
            concrete,
        )

    return op


@hugr_op(_map_op_for_global_var("GLOBAL_STATE"))
@no_type_check
def map_global_state_generic(func: Callable[[T, IN], OUT], inputs: IN) -> OUT: ...
