from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang_internals.compiler.core import EXTENSION_OPS_WITH_SIDE_EFFECTS
from guppylang_internals.decorator import hugr_op
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import ops
from hugr import tys as ht
from tket_exts import globals

T = guppy.type_var("T")
T_LIN = guppy.type_var("T", copyable=False, droppable=False)
IN = guppy.type_var("IN")
L_IN = guppy.type_var("L_IN", copyable=False, droppable=False)
OUT = guppy.type_var("OUT", copyable=False, droppable=False)

# Mark ops as having side effects to add order edges in the HUGR
# when calls return None.
# https://github.com/Quantinuum/guppylang/issues/1698
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.with")
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.map")


def with_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        assert len(concrete.input) == 2, (
            f"Expected 2 inputs args, found {len(concrete.input)}."
        )
        global_arg = concrete.input[1].type_arg()

        if global_arg.ty.type_bound() != ht.TypeBound.Linear:
            raise TypeError(f"Global arg must be linear. Found {global_arg.ty}.")

        return globals.with_def.instantiate(
            [ht.StringArg(var_name), global_arg, ht.ListArg([]), ht.ListArg([])],
            concrete,
        )

    return op


@hugr_op(with_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _with_non_linear_global(func: Callable[[], None], init_global: T) -> T: ...


@hugr_op(with_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _with_linear_global(
    func: Callable[[], None], init_global: T_LIN @ owned
) -> T_LIN: ...


@guppy.overload(_with_linear_global, _with_non_linear_global)
def with_global(*args): ...


def _map_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        # The first input arg should be a function type with the global type as the last
        # input arg and optional inputs
        func_input_ty = concrete.input[0]
        assert isinstance(func_input_ty, ht.FunctionType), (
            f"Expected a function, found {func_input_ty}."
        )
        *input_args, global_arg = [inp.type_arg() for inp in func_input_ty.input]

        output_args = [out.type_arg() for out in concrete.output]

        return globals.map_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg,
                ht.ListArg(input_args),
                ht.ListArg(output_args),
            ],
            concrete,
        )

    return op


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_with_input(func: Callable[[IN, T_LIN], OUT], inputs: IN) -> OUT: ...


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_with_linear_input(
    func: Callable[[L_IN, T_LIN], OUT], inputs: L_IN
) -> OUT: ...


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_with_linear_input_no_output(
    func: Callable[[L_IN, T_LIN], None], inputs: L_IN
) -> None: ...


@hugr_op(_map_op_for_global_var("GUPPY_FT_GLOBAL"))
@no_type_check
def _map_global_no_input(func: Callable[[T_LIN], OUT]) -> OUT: ...


@guppy.overload(
    _map_global_with_input,
    _map_global_with_linear_input,
    _map_global_with_linear_input_no_output,
    _map_global_no_input,
)
def map_global(*args): ...  # type: ignore[valid-type]
