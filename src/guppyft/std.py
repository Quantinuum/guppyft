import ast
from collections.abc import Callable, Sequence
from typing import Generic, no_type_check

import hugr.tys as ht
from guppylang import guppy
from guppylang_internals.checker.expr_checker import ExprSynthesizer, synthesize_call
from guppylang_internals.compiler.core import CompilerContext
from guppylang_internals.decorator import custom_function, custom_type
from guppylang_internals.definition.custom import CustomCallChecker, CustomCallCompiler
from guppylang_internals.nodes import GlobalCall
from guppylang_internals.tys.arg import Argument, ConstArg
from guppylang_internals.tys.builtin import bool_type
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.const import ConstValue
from guppylang_internals.tys.param import ConstParam
from guppylang_internals.tys.ty import (
    FuncInput,
    FunctionType,
    InputFlags,
    NumericType,
    OpaqueType,
    TupleType,
    Type,
)
from hugr import Wire
from hugr.ops import ExtOp

from guppyft.extensions import std_ops, std_types

OPS_EXTN = std_ops()
TYPES_EXTN = std_types()


def _std_ty(
    ty_name: str,
) -> Callable[[Sequence[Argument], CompilerContext], ht.Type]:
    def ty(args: Sequence[Argument], ctx: ToHugrContext) -> ht.Type:
        [k_arg] = args
        assert isinstance(k_arg, ConstArg)
        return ht.ExtType(TYPES_EXTN.get_type(ty_name), [k_arg.to_hugr(ctx)])

    return ty


N = guppy.nat_var("N")


class DecodeChecker(CustomCallChecker):
    """Call checker for `LogicalMeasurement.decode`.

    The arity of the returned tuple is `k`, the receiver's own generic `nat`
    argument, which is only known once `self`'s concrete type is resolved --
    Python's type system can't express a tuple's static length in terms of a
    nat generic, so this is computed dynamically here instead.
    """

    def synthesize(self, args: list[ast.expr]) -> tuple[ast.expr, Type]:
        [self_arg] = args
        _, self_ty = ExprSynthesizer(self.ctx).synthesize(self_arg)
        assert isinstance(self_ty, OpaqueType)
        [k_arg] = self_ty.args
        assert isinstance(k_arg, ConstArg)
        assert isinstance(k_arg.const, ConstValue)
        k = k_arg.const.value

        func_ty = FunctionType(
            inputs=[FuncInput(self_ty, InputFlags.NoFlags)],
            output=TupleType([bool_type()] * k),
        )

        args, ty, inst = synthesize_call(func_ty, args, self.node, self.ctx)
        return GlobalCall(def_id=self.func.id, args=args, type_args=inst), ty


class DecodeCompiler(CustomCallCompiler):
    """Call compiler for `LogicalMeasurement.decode`.

    Built as a plain `CustomCallCompiler` (rather than `OpCompiler`) because
    `OpCompiler.compile_with_inouts` derives `num_returns` from
    `self.func.ty.output`, which is a dummy `NoneType` when `has_signature`
    is False (as it is here, since a custom checker is used) -- this would
    misclassify all of `decode`'s outputs as "inout" wires. Building the
    `ExtOp` directly from `self.ty` (the real, dynamically-computed per-call
    signature) avoids that bug.
    """

    def compile(self, args: list[Wire]) -> list[Wire]:
        [self_ty] = self.ty.input
        assert isinstance(self_ty, ht.ExtType)
        k_arg = self_ty.args[0]
        assert isinstance(k_arg, ht.BoundedNatArg)
        # The op's second type argument is an explicit row of `k` `Bool`
        # types, substituted into the output tuple's row variable (see
        # `extensions/src/std/ops.rs`). This keeps the op's signature a
        # plain, serializable `PolyFuncTypeRV` rather than a `SignatureFromArgs`
        # binary that would be lost across a serialization round-trip.
        row_arg = ht.ListArg([ht.TypeTypeArg(ht.Bool)] * k_arg.n)
        op = ExtOp(OPS_EXTN.get_op("decode"), self.ty, [k_arg, row_arg])
        node = self.builder.add_op(op, *args)
        return list(node)


@custom_type(
    _std_ty("logical_measurement"),
    copyable=True,
    droppable=True,
    params=[ConstParam(1, "k", NumericType(NumericType.Kind.Nat))],
)
class LogicalMeasurement(Generic[N]):  # type: ignore[misc]
    # The real arity of the returned tuple is `k` (the receiver's `N`), which
    # is only known once `self`'s concrete type is resolved. Python's type
    # system can't express a tuple's static length in terms of a nat generic
    # (unlike `with_global`/`map_global` in `guppyft.globals`, an `@overload`
    # here isn't possible: those branch on a callback's own declared return
    # type via `ParamSpec`/`TypeVarTuple`, whereas `decode` has a single call
    # shape with no such generic to hang the arity off). The `tuple[bool, ...]`
    # annotation below is purely for IDE/mypy purposes; `@no_type_check` means
    # mypy doesn't actually enforce it. The real per-call return type is
    # computed dynamically by `DecodeChecker`.
    @custom_function(
        compiler=DecodeCompiler(), checker=DecodeChecker(), higher_order_value=False
    )
    @no_type_check
    def decode(self) -> tuple[bool, ...]:
        """Decode logical measurement"""
