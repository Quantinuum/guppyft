from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Self, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import link_name
from hugr import Hugr
from hugr.build import DefinitionBuilder
from hugr.ops import FuncDecl, FuncDefn
from hugr.package import Package

from guppyft._bindings import RsHugr
from guppyft._bindings import _implement_ops as _implement_ops_binding
from guppyft._util import get_link_name


class OpReplacements:
    ops: dict[
        tuple[str, str],
        tuple[GuppyFunctionDefinition[Any, Any] | Hugr[Any] | None, str],
    ]
    """Stores the operations to replace during op implementation and the implementation
    functions. A function can be set to `None` to indicate that a declaration with the
    given name should be generated instead."""

    def __init__(self) -> None:
        self.ops = {}

    def __iter__(
        self,
    ) -> Iterator[
        tuple[
            tuple[str, str],
            tuple[GuppyFunctionDefinition[Any, Any] | Hugr[Any] | None, str],
        ]
    ]:
        return iter(self.ops.items())

    def with_func(
        self, op: tuple[str, str], func: GuppyFunctionDefinition[Any, Any]
    ) -> Self:
        self.ops[op] = (func, get_link_name(func))

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

    def gen_missing_decls_from_lib(self, lib: Package) -> Self:
        # Build index of names missing declaration/definition
        missing: dict[str, tuple[str, str]] = {
            f_name: op_key
            for op_key, (func_opt, f_name) in self.ops.items()
            if func_opt is None
        }
        if not missing:
            return self

        for module in lib.modules:
            for _, data in module.nodes():
                if isinstance(data.op, FuncDefn) and data.op.f_name in missing:
                    op_key = missing.pop(data.op.f_name)
                    h: Hugr[Any] = Hugr()
                    DefinitionBuilder(h).module_root_builder().declare_function(
                        data.op.f_name, data.op.signature, data.op.visibility
                    )
                    self.ops[op_key] = (h, data.op.f_name)
                    if not missing:
                        return self

        return self


@dataclass(frozen=True, kw_only=True)
class ImplementOpsSpec:
    """A specification for the implement ops pass, supplying implementations to a set of
    HUGR extension ops."""

    ops: OpReplacements
    """The operations to replace."""
    build_wrapper: Callable[
        [GuppyFunctionDefinition[[], None]], GuppyFunctionDefinition[[], None]
    ] = field(default=lambda x: x)
    """Allows creating a wrapper around the transformed program, e.g. to setup and
    teardown the environment required for the op implementations."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the transformed program."""


def _to_rs_hugr(
    func_opt: GuppyFunctionDefinition[Any, Any] | Hugr[Any],
) -> RsHugr:
    match func_opt:
        case GuppyFunctionDefinition():
            return RsHugr.from_bytes(func_opt.compile_function().modules[0].to_bytes())
        case Hugr():
            return RsHugr.from_bytes(func_opt.to_bytes())
        case _:
            raise TypeError(
                f"Expected GuppyFunctionDefinition or Hugr, "
                f"got {type(func_opt)}: {func_opt}"
            )


def _implement_ops(pkg: Package, ops: OpReplacements) -> Package:
    rs_hugr = RsHugr.from_bytes(pkg.modules[0].to_bytes())

    rs_ops = {
        key: (
            func_opt if func_opt is None else _to_rs_hugr(func_opt),
            name,
        )
        for key, (func_opt, name) in ops
    }

    _implement_ops_binding(rs_hugr, rs_ops)

    return Package.from_bytes(rs_hugr.to_bytes())


def implement_ops(
    hugr_pkg: Package,
    spec: ImplementOpsSpec,
) -> Package:
    """
    Enriches the given package using the given spec by replacing all operations in the
    program with function calls to the functions in `spec.ops`.

    :param hugr_pkg: A package containing a single module.
    :param spec: The spec for the encoding. See `EnrichmentSpec` for details.
    :return: The enriched function as an executable HUGR package.
    """
    assert len(hugr_pkg.modules) == 1
    hugr = hugr_pkg.modules[0]

    entrypoint_op = hugr.entrypoint_op()
    assert isinstance(entrypoint_op, (FuncDefn, FuncDecl)), (
        "Provided a non-function entrypoint HUGR!"
    )

    # Add function declaration for missing ops to use during type replacement
    for lib in spec.libs:
        spec.ops.gen_missing_decls_from_lib(lib)

    # Reset entrypoint, marking module as non-executable, to avoid linking conflicts
    hugr.entrypoint = hugr.module_root
    # Run rewrite, replacing ops with function calls to the functions in `spec.ops`
    hugr_pkg = _implement_ops(hugr_pkg, spec.ops)

    # Build, compile, and link wrapper program
    @guppy.declare
    @link_name(entrypoint_op.f_name)
    @no_type_check
    def func_decl() -> None: ...

    wrapper = spec.build_wrapper(func_decl)
    pkg: Package = wrapper.compile()
    pkg = pkg.link(hugr_pkg, *spec.libs)
    assert isinstance(pkg, Package)  # Assert type for type checker

    return pkg
