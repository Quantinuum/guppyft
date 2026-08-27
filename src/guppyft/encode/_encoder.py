from dataclasses import dataclass, field
from typing import Any, Self

from guppylang.defs import GuppyFunctionDefinition
from hugr import Hugr
from hugr.ext import ExtensionRegistry
from hugr.package import Package
from hugr.passes.composable import ComposablePass, PassResult, implement_pass_run
from hugr.passes.scope import PassScope

from guppyft._bindings import RsHugr, _replace_encoder
from guppyft._util import extension_registry_to_json


@dataclass
class ReplaceEncoder(ComposablePass):
    """A composable pass that replaces extension ops in a `Hugr` according to
    the given mappings.

    See `guppyft._bindings._replace_encoder` for details on the replacement semantics.
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

    def run(self, hugr: Hugr[Any], *, inplace: bool = True) -> PassResult:
        return implement_pass_run(
            self,
            hugr=hugr,
            inplace=inplace,
            copy_call=lambda h: self._run_encode(h, inplace),
        )

    def with_scope(self, scope: PassScope) -> Self:
        """Set the scope of this pass and return self."""
        return self

    def _run_encode(self, hugr: Hugr[Any], inplace: bool) -> PassResult:
        def to_rs_hugr(
            repl: Hugr[Any] | GuppyFunctionDefinition[[Any], Any] | Package,
        ) -> RsHugr:
            match repl:
                case GuppyFunctionDefinition():
                    return RsHugr.from_bytes(
                        repl.compile_function().modules[0].to_bytes()
                    )
                case Hugr() | Package():
                    return RsHugr.from_bytes(repl.to_bytes())
                case _:
                    raise TypeError(
                        "Expected Hugr or GuppyFunctionDefinition or Package"
                        f", got {type(repl)}: {repl}"
                    )

        registry_str = (
            extension_registry_to_json(self.extensions) if self.extensions else None
        )
        rs_hugr = to_rs_hugr(hugr)
        rs_compound_op_replacements = {
            op: to_rs_hugr(repl) for op, repl in self.compound_op_replacements.items()
        }
        _replace_encoder(
            rs_hugr,
            self.op_replacements,
            rs_compound_op_replacements,
            self.ty_replacements,
            registry_str,
        )
        new_hugr = Hugr.from_bytes(rs_hugr.to_bytes())
        return PassResult.for_pass(self, hugr=new_hugr, inplace=inplace, result=None)
