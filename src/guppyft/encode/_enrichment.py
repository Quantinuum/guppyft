from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Self, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from hugr.ops import FuncDecl, FuncDefn
from hugr.package import Package

from guppyft._bindings import RsHugr
from guppyft._bindings import _replace_ops as _replace_ops_binding
from guppyft._util import link_name


class OpReplacements:
    ops: dict[tuple[str, str], tuple[GuppyFunctionDefinition[Any, Any] | None, str]]
    """Stores the operations to replace during encoding and their replacement functions.
    A function can be set to `None` to indicate that a declaration with the given name
    should be generated."""

    def __init__(self) -> None:
        self.ops = {}

    def __iter__(
        self,
    ) -> Iterator[
        tuple[tuple[str, str], tuple[GuppyFunctionDefinition[Any, Any] | None, str]]
    ]:
        return iter(self.ops.items())

    def with_func(
        self, op: tuple[str, str], func: GuppyFunctionDefinition[Any, Any]
    ) -> Self:
        self.ops[op] = (func, link_name(func))

        return self

    def with_funcs(
        self, funcs: dict[tuple[str, str], GuppyFunctionDefinition[Any, Any]]
    ) -> Self:
        for op, func in funcs.items():
            self.with_func(op, func)

        return self

    def with_generated_decl(self, op: tuple[str, str], func_name: str) -> Self:
        self.ops[op] = (None, func_name)

        return self

    def with_generated_decls(self, names: dict[tuple[str, str], str]) -> Self:
        for op, name in names.items():
            self.with_generated_decl(op, name)

        return self


@dataclass(frozen=True, kw_only=True)
class EnrichmentSpec:
    ops: OpReplacements
    """The operations to replace."""
    build_wrapper: Callable[
        [GuppyFunctionDefinition[[], None]], GuppyFunctionDefinition[[], None]
    ] = field(default=lambda x: x)
    """Allows creating a wrapper around the enriched program, e.g. to setup and teardown
    the required environment."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the enriched program."""


def _replace_ops(pkg: Package, ops: OpReplacements) -> Package:
    rs_hugr = RsHugr.from_bytes(pkg.modules[0].to_bytes())

    rs_ops = {
        key: (
            func_opt
            if func_opt is None
            else RsHugr.from_bytes(func_opt.compile_function().modules[0].to_bytes()),
            name,
        )
        for key, (func_opt, name) in ops
    }

    _replace_ops_binding(rs_hugr, rs_ops)

    return Package.from_bytes(rs_hugr.to_bytes())


def enrich(
    hugr_pkg: Package,
    spec: EnrichmentSpec,
) -> Package:
    """
    Encodes the given function using the given spec by replacing all operations in the
    program with function calls to the functions in `spec.ops`.

    :param hugr_pkg: A package containing a single module.
    :param spec: The spec for the encoding. See `EncoderSpec` for details.
    :param passes: Tket passes to run on the unencoded program, before passes from the
        spec. The default is a single run of `tket.passes.NormalizeGuppy`.
    :return: The compiled, encoded function as an executable HUGR package.
    """
    assert len(hugr_pkg.modules) == 1
    hugr = hugr_pkg.modules[0]

    entrypoint_op = hugr.entrypoint_op()
    assert isinstance(entrypoint_op, (FuncDefn, FuncDecl)), (
        "Provided a non-function entrypoint HUGR!"
    )

    # Reset entrypoint, marking module as non-executable, to avoid linking conflicts
    hugr.entrypoint = hugr.module_root
    # Run rewrite, replacing ops with function calls to the functions in `spec.ops`
    hugr_pkg = _replace_ops(hugr_pkg, spec.ops)

    # Build, compile, and link wrapper program
    @guppy.declare(link_name=entrypoint_op.f_name)
    @no_type_check
    def func_decl() -> None: ...

    wrapper = spec.build_wrapper(func_decl)
    pkg: Package = wrapper.compile()
    pkg = pkg.link(hugr_pkg, *spec.libs)
    assert isinstance(pkg, Package)  # Assert type for type checker

    return pkg
