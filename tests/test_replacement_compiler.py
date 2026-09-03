from typing import Any

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.platform import output
from guppylang.std.quantum import h, measure, qubit
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
