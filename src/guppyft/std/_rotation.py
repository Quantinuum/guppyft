from guppylang_internals.compiler.builder import pure
from guppylang_internals.compiler.builder.ops import unpack_tuple
from guppylang_internals.definition.value import CallReturnWires
from guppylang_internals.std._internal.compiler.quantum import (
    RotationCompiler,
    from_halfturns_unchecked,
)
from hugr import Wire
from hugr import tys as ht
from hugr.ext import Extension
from hugr.std.float import FLOAT_T
from tket_exts import tket

from guppyft.code._logical import _logical_op

rotation_ext_def = tket.rotation.RotationExtension()
ROTATION_EXTENSION = rotation_ext_def()
ROTATION_T_DEF = ROTATION_EXTENSION.get_type("rotation")
ROTATION_T = ht.ExtType(ROTATION_T_DEF)


class _RotationCompiler(RotationCompiler):
    ext: Extension

    def __init__(self, opname: str, ext: Extension):
        self.opname = opname
        self.ext = ext

    def compile_with_inouts(self, args: list[Wire]) -> CallReturnWires:

        [*qs, angle] = args
        [halfturns] = self.builder.add_op(unpack_tuple([FLOAT_T]), angle)
        [rotation] = self.builder.add_op(from_halfturns_unchecked(), halfturns)

        if not qs:
            func_ty = ht.FunctionType([ROTATION_T], [])
        else:
            qubit_ty = self.ty.input[0]
            func_ty = ht.FunctionType(
                [qubit_ty for _ in qs] + [ROTATION_T], self.ty.output
            )

        qs = self.builder.add_op(
            pure(
                _logical_op(self.opname, self.ext)(
                    func_ty,
                    (),
                    self.ctx,
                ),
            ),
            *qs,
            rotation,
        )

        return CallReturnWires(regular_returns=[], inout_returns=list(qs))
