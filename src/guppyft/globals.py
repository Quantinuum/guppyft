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


def with_op_for_global_var(
    var_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    def op(concrete: ht.FunctionType, args: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        assert len(concrete.input) == 2, (
            f"Expected 2 inputs args, found {len(concrete.input)}."
        )
        global_arg = concrete.input[0].type_arg()

        if global_arg.ty.type_bound() != ht.TypeBound.Linear:
            raise TypeError(f"Global arg must be linear. Found {global_arg.ty}.")

        return globals.with_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg,
                ht.ListArg([]),
                ht.ListArg([]),
                ht.ListArg([]),
            ],
            concrete,
        )

    return op


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_non_linear_global(init_global: State, func: Callable[[], None]) -> State: ...


@hugr_op(with_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _with_linear_global(
    init_global: State_Linear @ owned, func: Callable[[], None]
) -> State_Linear: ...


@guppy.overload(_with_linear_global, _with_non_linear_global)
def with_global_state(state: Any, func: Callable[[], None]) -> Any: ...


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

        global_arg = func_input_args[0]

        # The function should have at most two inputs. This should be enforced
        # by the Guppy overloads.
        assert len(func_input_args) <= 2

        if len(func_input_args) == 2:
            op_input_arg = func_input_args[1:]

            # If the input is linear, we need to separate the output into explicit and
            # implicit returns to correctly initialise the signature of the HUGR op
            if op_input_arg[0].ty.type_bound() == ht.TypeBound.Linear:
                # The mapped function can only have a single input argument. If the
                # input is linear, the explicit output args must be all but the
                # element (i.e. [:-1]), while the implicit output arg is the last
                # element (i.e. [-1]).
                explicit_output_args = output_args[:-1]
                implicit_output_arg = [output_args[-1]]
            else:
                explicit_output_args = output_args
                implicit_output_arg = []
        else:
            op_input_arg = []
            explicit_output_args = output_args
            implicit_output_arg = []

        return globals.map_def.instantiate(
            [
                ht.StringArg(var_name),
                global_arg,
                ht.ListArg(list[ht.TypeArg](op_input_arg)),
                ht.ListArg(list[ht.TypeArg](explicit_output_args)),
                ht.ListArg(list[ht.TypeArg](implicit_output_arg)),
            ],
            concrete,
        )

    return op


@hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _map_global_with_nonlinear_input(
    func: Callable[[State_Linear, In], Out], inputs: In
) -> Out: ...


@hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _map_global_with_linear_input(
    func: Callable[[State_Linear, In_Linear], Out], inputs: In_Linear
) -> Out: ...


@hugr_op(_map_op_for_global_var(GLOBAL_VAR_NAME))
@no_type_check
def _map_global_no_input(func: Callable[[State_Linear], Out]) -> Out: ...


@guppy.overload(
    _map_global_with_nonlinear_input,
    _map_global_with_linear_input,
    _map_global_no_input,
)
def map_global_state(func: Any, inputs: Any | None = None) -> Any: ...
