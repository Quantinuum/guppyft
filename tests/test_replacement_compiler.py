from typing import Any, no_type_check

import pytest
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder
from guppylang.std.angles import angle
from guppylang.std.platform import output
from guppylang.std.quantum import h, measure, qubit, rz
from hugr import Hugr
from hugr.build import Module
from hugr.std import _std_extensions

from guppyft.encode import ReplacementCompiler


def _wrap_func(func: GuppyFunctionDefinition[[qubit], None]) -> Hugr[Any]:
    """Wrap the given function via a proxy."""
    fn_hugr = func.compile_function().modules[0]
    func_node = fn_hugr.entrypoint
    func_op = fn_hugr.entrypoint_op()

    wrapper = Module(fn_hugr).define_function(
        f"{func_op.f_name}_wrapper", func_op.inputs
    )

    call_node = wrapper.call(func_node, *wrapper.inputs())
    wrapper.set_outputs(*call_node.outputs())
    fn_hugr.entrypoint = wrapper.parent_node

    return fn_hugr


def test_replace_with_wrapped() -> None:
    @guppy
    def _h(q: qubit) -> None:
        h(q)

    compiler = ReplacementCompiler(
        op_replacements={},
        compound_op_replacements={("tket.quantum", "H"): _wrap_func(_h)},
        extensions=_std_extensions(),
    )

    @guppy
    def main() -> None:
        q = qubit()
        h(q)
        output("q", measure(q).read())

    pkg = main.with_minimal_opt().compile()
    compiler.compile(pkg)  # Smoke test


@pytest.mark.parametrize("adapt_rotation_inputs", [False, True])
def test_replace_rotation_with_angle_function(adapt_rotation_inputs: bool) -> None:
    @guppy
    def replacement(q: qubit, phase: angle) -> None:
        output("phase", phase.halfturns)
        rz(q, phase)

    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        rz(q, angle(0.13))
        rz(q, angle(-0.31))
        q.discard()

    compiler = ReplacementCompiler(
        op_replacements={},
        compound_op_replacements={
            ("tket.quantum", "Rz"): replacement.compile_function()
        },
        extensions=_std_extensions(),
        adapt_rotation_inputs=adapt_rotation_inputs,
    )
    pkg = main.with_minimal_opt().compile()
    if not adapt_rotation_inputs:
        with pytest.raises(ValueError, match="does not have the expected signature"):
            compiler.compile(pkg)
        return
    pkg = compiler.compile(pkg)
    results = EmulatorBuilder().build(pkg, n_qubits=1).run().collated_shots()
    assert results == [{"phase": [0.13, -0.31]}]
