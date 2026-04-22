from typing import Any, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang_internals.definition.declaration import CheckedFunctionDecl
from guppylang_internals.definition.function import ParsedFunctionDef
from guppylang_internals.engine import ENGINE
from hugr.package import Package
from tket.passes import NormalizeGuppy

from guppyft._bindings import RsHugr
from guppyft._bindings import _replace_ops as _replace_ops_binding
from guppyft.definition import CodeDefinition


def _replace_ops(
    hugr: Package,
    ops: dict[tuple[str, str], tuple[GuppyFunctionDefinition[Any, Any], str]],
) -> Package:
    rs_hugr = RsHugr.from_bytes(hugr.modules[0].to_bytes())

    rs_ops = {
        key: (RsHugr.from_bytes(val.compile_function().modules[0].to_bytes()), name)
        for key, (val, name) in ops.items()
    }

    _replace_ops_binding(rs_hugr, rs_ops)

    return Package.from_bytes(rs_hugr.to_bytes())


def determine_link_name(func: GuppyFunctionDefinition[Any, Any]) -> str:
    match ENGINE.get_parsed(func.id):
        case ParsedFunctionDef(link_name=link_name):
            return link_name
        case CheckedFunctionDecl(link_name=link_name):
            return link_name
        case _:
            raise ValueError(f"Unknown link name for function with ID {func.id}")


def encode(
    comp_func_defn: GuppyFunctionDefinition[[], None],
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
    identified_logical_ops = {
        key: (func, determine_link_name(func))
        for key, func in definition.logical_ops.items()
    }
    comp_pkg = _replace_ops(comp_pkg, identified_logical_ops)

    # Build wrapper program
    @guppy.declare(link_name=determine_link_name(comp_func_defn))
    @no_type_check
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
    assert isinstance(pkg, Package)  # Assert type for type checker

    return pkg
