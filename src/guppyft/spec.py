from dataclasses import dataclass, field
from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr.ext import Extension
from hugr.package import Package
from hugr.passes.composable import ComposablePass


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    logical_ops: dict[tuple[str, str], GuppyFunctionDefinition[Any, Any]]
    setup: GuppyFunctionDefinition[[], None]
    teardown: GuppyFunctionDefinition[[], None]
    tket_passes: list[ComposablePass]
    wrapper_extensions: list[Extension] = field(default_factory=list)
    libs: list[Package] = field(default_factory=list)
