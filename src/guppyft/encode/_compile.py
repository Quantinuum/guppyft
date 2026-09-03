from dataclasses import dataclass, field
from typing import Any, Protocol

from guppylang.defs import GuppyFunctionDefinition
from hugr import Hugr
from hugr.ext import ExtensionRegistry
from hugr.package import Package

from guppyft._bindings import _replacement_compiler_impl
from guppyft._util import extension_registry_to_json
from guppyft.encode._util import to_rs_hugr


class LogicalCompiler(Protocol):
    def __call__(self, pkg: Package) -> Package:
        return self.compile(pkg)

    def compile(self, pkg: Package) -> Package: ...


@dataclass(frozen=True)
class ReplacementCompiler(LogicalCompiler):
    """A composable pass that replaces extension ops in a `Hugr` according to the given
    mappings.

    See `guppyft._bindings._replacement_compiler_impl` for semantic details.
    """

    op_replacements: dict[tuple[str, str], tuple[str, str, list[int | str]]]
    """Maps each source `(extension_name, op_name)` pair (taking no type args)
    to a target `(extension_name, op_name, args)` triple, where `args` is the
    list of type args (integers or strings) used to instantiate the target
    op."""
    compound_op_replacements: dict[
        tuple[str, str], Hugr[Any] | GuppyFunctionDefinition[[Any], Any] | Package
    ] = field(default_factory=dict)
    """Replaces each source `(extension_name, op_name)` pair (taking no type args)
    with the given HUGR. When a Guppy function is given as a replacement, it is
    compiled to HUGR first."""
    ty_replacements: dict[tuple[str, str], tuple[str, str]] = field(
        default_factory=dict
    )
    """Optional mapping between src and tgt types to be replaced globally during
    encoding where types are provided in the form `(extension_name, ty_name)`.
    """
    extensions: ExtensionRegistry | None = None
    """Optional JSON-encoded list of additional extension definitions, used to
    resolve target ops/types that are not already registered on the input Hugr."""

    def __post_init__(self) -> None:
        duplicates = self.op_replacements.keys() & self.compound_op_replacements.keys()
        if duplicates:
            raise ValueError(
                "Duplicate op replacement(s) found in both `op_replacements` and "
                f"`compound_op_replacements`: {sorted(duplicates)}"
            )
        for op, repl in self.compound_op_replacements.items():
            if isinstance(repl, Package) and len(repl.modules) != 1:
                raise ValueError(
                    f"Package replacement for op {op} must contain exactly one "
                    f"module, got {len(repl.modules)}"
                )

    def compile(self, pkg: Package) -> Package:
        rs_hugr = to_rs_hugr(pkg)
        rs_compound_op_replacements = {
            op: to_rs_hugr(repl) for op, repl in self.compound_op_replacements.items()
        }
        _replacement_compiler_impl(
            rs_hugr,
            self.op_replacements,
            rs_compound_op_replacements,
            self.ty_replacements,
            extension_registry_to_json(self.extensions) if self.extensions else None,
        )
        return Package.from_bytes(rs_hugr.to_bytes())
