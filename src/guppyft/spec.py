from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import Any, Self

from guppylang.defs import GuppyFunctionDefinition
from hugr.package import Package
from hugr.passes.composable import ComposablePass

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
class EncoderSpec:
    ops: OpReplacements
    """The operations to encode / replace."""
    build_wrapper: Callable[
        [GuppyFunctionDefinition[[], None]], GuppyFunctionDefinition[[], None]
    ] = field(default=lambda x: x)
    """Allows creating a wrapper around the encoded program, e.g. to setup and teardown
    the required environment."""
    tket_passes: list[ComposablePass] = field(default_factory=list)
    """Additional tket passes to run on the unencoded program."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the encoded program."""
