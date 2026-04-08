from dataclasses import dataclass, field

from guppylang.defs import GuppyFunctionDefinition
from hugr.ext import Extension
from hugr.package import Package
from hugr.passes.composable import ComposablePass


@dataclass(frozen=True, kw_only=True)
class CodeDefinition:
    logical_ops: dict[tuple[str, str], GuppyFunctionDefinition]
    setup: GuppyFunctionDefinition
    teardown: GuppyFunctionDefinition
    tket_passes: list[ComposablePass]
    wrapper_extensions: list[Extension] = field(default_factory=list)
    libs: list[Package] = field(default_factory=list)
