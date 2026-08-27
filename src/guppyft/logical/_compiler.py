from collections.abc import Callable

import hugr.tys as ht
from guppylang_internals.definition.custom import CustomInoutCallCompiler
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import Wire, ops
from hugr.ext import Extension
from hugr.std.float import FLOAT_T
from tket_exts import tket

rotation = tket.rotation.RotationExtension()
ROTATION_EXTENSION = rotation()
ROTATION_T_DEF = ROTATION_EXTENSION.get_type("rotation")
ROTATION_T = ht.ExtType(ROTATION_T_DEF)


def from_halfturns_unchecked() -> ops.ExtOp:
    return ops.ExtOp(
        ROTATION_EXTENSION.get_op("from_halfturns_unchecked"),
        ht.FunctionType([FLOAT_T], [ROTATION_T]),
    )


def logical_op(
    op_name: str,
    ext: Extension,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], ops.DataflowOp]:
    """Utility method to create Hugr logical ops.

    args:
        op_name: The name of the operation.
        ext: The extension of the operation.

    Returns:
        A function that takes an instantiation of the type arguments and returns
        a concrete HUGR op.
    """
    op_def = ext.get_op(op_name)

    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> ops.DataflowOp:
        return ops.ExtOp(op_def, ty, [arg.to_hugr(ctx) for arg in inst])

    return op


class RotationCompiler(CustomInoutCallCompiler):
    opname: str
    ext: Extension

    def __init__(self, opname: str, ext: Extension):
        self.opname = opname
        self.ext = ext

    def compile_with_inouts(self, args: list[Wire]) -> CallReturnWires:

        [*qs, angle] = args
        [halfturns] = self.builder.add_op(ops.UnpackTuple([FLOAT_T]), angle)
        [rotation] = self.builder.add_op(from_halfturns_unchecked(), halfturns)

        op_def = self.ext.get_op(self.opname)
        if not qs:
            func_ty = ht.FunctionType([ROTATION_T], [])
        else:
            poly_func = op_def.signature.poly_func
            if poly_func is None:
                raise ValueError(
                    f"Operation {self.opname} has no static signature "
                    f"to infer qubit type from."
                )
            qubit_ty = poly_func.body.input[0]
            func_ty = ht.FunctionType(
                [qubit_ty for _ in qs] + [ROTATION_T], [qubit_ty for _ in qs]
            )

        qs = self.builder.add_op(
            logical_op(self.opname, self.ext)(
                func_ty,
                (),
                self.ctx,
            ),
            *qs,
            rotation,
        )
        return CallReturnWires(regular_returns=[], inout_returns=list(qs))
