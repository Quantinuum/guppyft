from guppy_ft_encoder import replace_ops
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang_internals.definition.function import ParsedFunctionDef
from guppylang_internals.engine import ENGINE
from hugr.package import Package
from tket.passes import NormalizeGuppy

from guppyft.definition import CodeDefinition


def auto_encode(
    comp_func_defn: GuppyFunctionDefinition,
    definition: CodeDefinition,
) -> Package:
    # Compile computational program with entrypoint since NormalizeGuppy needs it
    comp_pkg: Package = comp_func_defn.compile_function()

    # Run normalise and all optimisation passes
    normalize_pass = NormalizeGuppy()
    comp_pkg.modules[0] = normalize_pass(comp_pkg.modules[0], inplace=False)
    for optimisation in definition.tket_passes:
        comp_pkg.modules[0] = optimisation(comp_pkg.modules[0], inplace=False)

    # Reset entrypoint to mark module as non-executable to avoid conflicts
    comp_pkg.modules[0].entrypoint = comp_pkg.modules[0].module_root
    # Run rewrite, replacing ops with function calls to the functions in`logical_ops`
    comp_pkg = replace_ops(comp_pkg, definition.logical_ops)

    # Build wrapper program
    parsed_comp_def = ENGINE.get_parsed(comp_func_defn.id)
    assert isinstance(parsed_comp_def, ParsedFunctionDef)
    comp_func_name = parsed_comp_def.link_name

    # Placeholder computational program
    @guppy.declare(link_name=comp_func_name)
    def comp_prog_decl() -> None: ...

    setup_func = definition.setup
    teardown_func = definition.teardown

    @guppy
    def main_wrapper() -> None:
        setup_func()
        comp_prog_decl()
        teardown_func()

    # Compile to HUGR
    pkg: Package = main_wrapper.compile()
    pkg.extensions.extend(definition.wrapper_extensions)
    pkg = pkg.link(comp_pkg, *definition.libs)

    return pkg
