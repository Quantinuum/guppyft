from dataclasses import dataclass
from typing import Any, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.angles import angle
from guppylang.std.quantum import cx, h, qubit, t, tdg
from hugr import Hugr, ops, tys
from hugr.build import Module
from hugr.passes.composable import ComposablePass, PassResult, implement_pass_run
from hugr.passes.scope import PassScope
from hugr.std import _std_extensions
from hugr.std.float import FLOAT_T
from tket_exts import rotation

from guppyft.decompose._comparator_based_rz import (
    comparator_based_rz_cascade,
    n_comparator_based_rz_cascade_ancillas,
)
from guppyft.encode import ReplacementCompiler


@dataclass(frozen=True, kw_only=True)
class ComparatorRzDecomposer(ComposablePass):
    """Decomposes Rz gates using $2*ceil(log2(1/epsilon))$ ancilla qubits via
    comparators and repeat-until-success. Introduces Toffoli gates.
    Can be used to decompose angles at runtime.
    See https://arxiv.org/pdf/2404.05618."""

    epsilon: float

    def num_ancilla(self) -> int:
        """Number of ancilla qubits required for the target precision (epsilon)."""
        return n_comparator_based_rz_cascade_ancillas(self.epsilon)

    def run(self, hugr: Hugr[Any], *, inplace: bool = True) -> PassResult:
        return implement_pass_run(
            self,
            hugr=hugr,
            inplace=inplace,
            copy_call=lambda _hugr: self._run_impl(_hugr),
        )

    def _run_impl(self, hugr: Hugr[Any]) -> PassResult:
        compiler = ReplacementCompiler(
            op_replacements={},
            compound_op_replacements={
                ("tket.quantum", "Rz"): _compile_rotation_func(
                    comparator_based_rz_cascade(self.epsilon)
                )
            },
            extensions=_std_extensions(),
        )
        [module] = compiler.compile(hugr.to_package()).modules

        return PassResult.for_pass(self, hugr=module, inplace=False, result=None)

    def with_scope(self, scope: PassScope) -> ComposablePass:
        return self


@guppy
@no_type_check
def _toffoli_decomposition(ctrl0: qubit, ctrl1: qubit, target: qubit) -> None:
    h(target)
    cx(ctrl1, target)
    tdg(target)
    cx(ctrl0, target)
    t(target)
    cx(ctrl1, target)
    tdg(target)
    cx(ctrl0, target)
    t(ctrl1)
    t(target)
    h(target)
    cx(ctrl0, ctrl1)
    t(ctrl0)
    tdg(ctrl1)
    cx(ctrl0, ctrl1)


@dataclass(frozen=True)
class ToffoliDecomposer(ComposablePass):
    """Decomposes Toffoli gates into Clifford+T gates. Each Toffoli uses 7 T gates."""

    def run(self, hugr: Hugr[Any], *, inplace: bool = True) -> PassResult:
        return implement_pass_run(
            self,
            hugr=hugr,
            inplace=inplace,
            copy_call=lambda _hugr: self._run_impl(_hugr),
        )

    def _run_impl(self, hugr: Hugr[Any]) -> PassResult:
        compiler = ReplacementCompiler(
            op_replacements={},
            compound_op_replacements={
                ("tket.quantum", "Toffoli"): _toffoli_decomposition
            },
            extensions=_std_extensions(),
        )
        [module] = compiler.compile(hugr.to_package()).modules

        return PassResult.for_pass(self, hugr=module, inplace=False, result=None)

    def with_scope(self, scope: PassScope) -> ComposablePass:
        return self


def _compile_rotation_func(
    angle_function: GuppyFunctionDefinition[[qubit, angle], None],
) -> Hugr[Any]:
    """Compile an angle-based Guppy function for a TKET rotation operation.

    Guppy functions receive angles as `Tuple(float64)`, while TKET rotation
    operations receive the opaque `tket.rotation.rotation` type. The returned
    HUGR unwraps the rotation to half-turns before calling `angle_function`.
    """
    fn_hugr = angle_function.compile_function().modules[0]
    orig_func_defn_node = fn_hugr.entrypoint
    orig_func_defn_op = fn_hugr.entrypoint_op()
    angle_type = tys.Tuple(FLOAT_T)

    if not isinstance(orig_func_defn_op, ops.FuncDefn):
        raise TypeError("The angle_function must compile to a function definition")
    if not orig_func_defn_op.inputs or orig_func_defn_op.inputs[-1] != angle_type:
        raise ValueError(
            "The angle_function must take a guppylang.std.angles.angle "
            "as its final argument"
        )

    # Create a wrapper function that takes a TKET rotation and converts it
    # to an angle type before calling `angle_function`.
    wrapper = Module(fn_hugr).define_function(
        f"{orig_func_defn_op.f_name}_wrapper",
        [*orig_func_defn_op.inputs[:-1], rotation.rotation],
    )

    *args, rotation_arg = wrapper.inputs()
    halfturns = wrapper.add_op(rotation.to_halfturns, rotation_arg).out(0)
    angle = wrapper.add_op(ops.MakeTuple([FLOAT_T]), halfturns).out(0)
    call_node = wrapper.call(orig_func_defn_node, *args, angle)
    wrapper.set_outputs(*call_node.outputs())
    fn_hugr.entrypoint = wrapper.parent_node
    return fn_hugr
