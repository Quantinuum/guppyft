from dataclasses import dataclass
from typing import Any, no_type_check

from guppylang import guppy
from guppylang.std.quantum import cx, h, qubit, t, tdg
from hugr import Hugr
from hugr.passes.composable import ComposablePass, PassResult, implement_pass_run
from hugr.passes.scope import PassScope
from hugr.std import _std_extensions

from guppyft.encode import ReplacementCompiler


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
