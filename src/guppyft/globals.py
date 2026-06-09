from collections.abc import Callable
from typing import Any, no_type_check

from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang_internals.compiler.core import EXTENSION_OPS_WITH_SIDE_EFFECTS
from guppylang_internals.decorator import hugr_op
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import ops
from hugr import tys as ht
from tket_exts import globals

State = guppy.type_var("State", copyable=False, droppable=False)
# State_Linear = guppy.type_var("State_Linear", copyable=False, droppable=False)
# In = guppy.type_var("In")
In = guppy.type_var("In", copyable=False, droppable=False)
Out = guppy.type_var("OUT", copyable=False, droppable=False)

# Mark ops as having side effects to add order edges in the HUGR
# when calls return None.
# https://github.com/Quantinuum/guppylang/issues/1698
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.with")
EXTENSION_OPS_WITH_SIDE_EFFECTS.append("tket.globals.map")

GLOBAL_VAR_NAME = "guppy_ft_global"


def with_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        print("dougrulz")
        # assert len(concrete.input) == 2, (
        #     f"Expected 2 inputs args, found {len(concrete.input)}."
        # )
        # assert len(concrete.input) == 3
        global_ty = concrete.input[0]
        func_ty = concrete.input[1]
        assert isinstance(func_ty, ht.FunctionType), (
            f"Expected a function, found {func_ty}."
        )
        in_tys = func_ty.input
        out_tys = func_ty.output
        print(in_tys)
        print(out_tys)

        # assert len(concrete.output) == 2
        # assert global_ty == concrete.output[0]

        return globals.with_def.instantiate(
            [
                ht.StringArg(var_name),
                global_ty.type_arg(),
                ht.ListArg([t.type_arg() for t in in_tys]),
                ht.ListArg([t.type_arg() for t in out_tys]),
            ],
            concrete,
        )

    return op


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_no_input(
    init_global: State @ owned, func: Callable[[], Out]
) -> tuple[State, Out]: ...


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_input(
    init_global: State @ owned, func: Callable[[In @ owned], Out], inputs: In @ owned
) -> tuple[State, Out]: ...


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_input_no_output(
    init_global: State @ owned, func: Callable[[In @ owned], None], inputs: In @ owned
) -> State: ...


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_no_input_no_output(
    init_global: State @ owned, func: Callable[[], None]
) -> State: ...


# @hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
# @no_type_check
# def _with_linear_global(
#     init_global: State_Linear @ owned, func: Callable[[], None]
# ) -> State_Linear: ...


@guppy.overload(
    _with_no_input_no_output,
    _with_no_input,
    _with_input_no_output,
    _with_input,
)
def with_global_state(
    state: State @ owned, func: Any, inputs: Any @ owned | None = None
) -> Any: ...


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

        func_input_args = [inp.type_arg() for inp in func_input_ty.input]
        output_args = [out.type_arg() for out in concrete.output]
        global_ty = func_input_args[0]
        assert len(func_input_args) <= 2
        input_args = func_input_args[1:]
        # output_args = []
        # if len(func_output_args) == 1:
        #     a = func_output_args[0]
        #     if isinstance(a, ht.TupleType):
        #         assert a.elems[0] == global_ty
        #         output_args = a.elems[1:]
        #     else:
        #         assert a == global_ty
        #         output_args = []
        return globals.map_def.instantiate(
            [
                ht.StringArg(var_name),
                global_ty,
                ht.ListArg(input_args),
                ht.ListArg(output_args),
            ],
            concrete,
        )

    return op


# @hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
# @no_type_check
# def _map_global_with_nonlinear_input(
#     func: Callable[[State, In], tuple[Out], inputs: In
# ) -> Out: ...


@hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _map_global_with_input(
    func: Callable[[State @ owned, In @ owned], tuple[State, Out]],
    inputs: In @ owned,
) -> Out: ...


@hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _map_global_no_input(
    func: Callable[[State @ owned], tuple[State, Out]],
) -> Out: ...


@guppy.overload(
    _map_global_with_input,
    _map_global_no_input,
)
def map_global_state(func: Any, inputs: Any @ owned | None = None) -> Any: ...
