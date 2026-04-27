from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang.std.option import Option
from guppylang_internals.decorator import hugr_op
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import ops
from hugr import tys as ht
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


# TODO MOVE INTO CODES (maybe a default renaming)
@hugr_op(swap_op_for_global_var("GLOBAL_STATE"))
@no_type_check
def swap_global_state_generic(new_value: Option[T] @ owned) -> Option[T]: ...
