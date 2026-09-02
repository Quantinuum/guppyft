from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Self, no_type_check, overload

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import link_name
from hugr import Hugr
from hugr.build import DefinitionBuilder
from hugr.ext import TypeDef
from hugr.ops import FuncDecl, FuncDefn
from hugr.package import Package, link_packages
from hugr.tys import ExtType, Type
from tket.extensions import measurement

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


class TyReplacements:
    tys: set[tuple[str, str]]

    def __init__(self) -> None:
        self.tys = set()

    def with_type(self, ty: Type | tuple[str, str]) -> Self:
        match ty:
            case TypeDef():
                self.tys.add((ty.get_extension().name, ty.name))
            case ExtType():
                self.tys.add((ty.type_def.get_extension().name, ty.type_def.name))
            case tuple():
                self.tys.add(ty)
            case _:
                raise TypeError(f"TyReplacements: Unexpected Type: {ty}, {type(ty)}")

        return self

    def with_types(self, tys: Sequence[Type | tuple[str, str]]) -> Self:
        for ty in tys:
            self.with_type(ty)

        return self

    def with_defaults(self) -> Self:
        return self.with_types([measurement.measurement_t, ("prelude", "qubit")])


@dataclass(frozen=True, kw_only=True)
class ImplementOpsSpec:
    """A specification for the implement ops pass, supplying implementations to a set of
    HUGR extension ops."""

    ops: OpReplacements
    """The operations to replace."""
    tys: TyReplacements = field(
        default_factory=lambda: TyReplacements().with_defaults()
    )
    """The types to replace."""
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


def _implement_ops(
    pkg_bytes: bytes, ops: OpReplacements, tys: set[tuple[str, str]]
) -> bytes:
    rs_hugr = RsHugr.from_bytes(pkg_bytes)

    rs_ops = {
        key: (
            func_opt if func_opt is None else _to_rs_hugr(func_opt),
            name,
        )
        for key, (func_opt, name) in ops
    }

    _implement_ops_binding(rs_hugr, rs_ops, tys)

    return rs_hugr.to_bytes()


@overload
def implement_ops(
    hugr_pkg: Package, spec: ImplementOpsSpec, *, as_bytes: Literal[False] = False
) -> Package: ...
@overload
def implement_ops(
    hugr_pkg: Package, spec: ImplementOpsSpec, *, as_bytes: Literal[True]
) -> bytes: ...
def implement_ops(
    hugr_pkg: Package, spec: ImplementOpsSpec, *, as_bytes: bool = False
) -> Package | bytes:
    """
    Enriches the given package using the given spec by replacing all operations in the
    program with function calls to the functions in `spec.ops`.

    :param hugr_pkg: A package containing a single module.
    :param spec: The spec for the encoding. See `EnrichmentSpec` for details.
    :param as_bytes: Whether to return bytes instead of the Package, skipping the final
        deserialisation.
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
    hugr_pkg_bytes = _implement_ops(hugr.to_bytes(), spec.ops, spec.tys.tys)

    # Build, compile, and link wrapper program
    @guppy.declare
    @link_name(entrypoint_op.f_name)
    @no_type_check
    def func_decl() -> None: ...

    # We have to ensure the build wrapper is a function definition rather than a
    # declaration, so that the package contains an entrypoint. Guppy compiles
    # declarations to module-rooted HUGRs.
    wrapper = spec.build_wrapper(func_decl)

    @guppy
    def outer_wrapper() -> None:
        wrapper()

    pkg: Package = outer_wrapper.compile()
    pkg_bytes = link_packages(
        pkg.to_bytes(), hugr_pkg_bytes, *[lib.to_bytes() for lib in spec.libs]
    )

    if as_bytes:
        return pkg_bytes

    return Package.from_bytes(pkg_bytes)


@dataclass(frozen=True)
class ImplementOps:
    _runner: Callable[[Package, bool], Package]

    def __call__(self, pkg: Package, as_bytes: bool = False) -> Package:
        return self._runner(pkg, as_bytes)

    @staticmethod
    def for_spec(spec: ImplementOpsSpec) -> "ImplementOps":
        return ImplementOps.for_spec_generator(lambda _: spec)

    @staticmethod
    def for_spec_generator(
        spec_gen: Callable[[Package], ImplementOpsSpec],
    ) -> "ImplementOps":
        return ImplementOps(
            lambda pkg, as_bytes: implement_ops(pkg, spec_gen(pkg), as_bytes=as_bytes)  # type: ignore[call-overload]
        )
