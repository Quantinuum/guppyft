from dataclasses import dataclass, field
from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr.ext import Extension
from hugr.package import Package
from hugr.passes.composable import ComposablePass


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    logical_ops: dict[tuple[str, str], GuppyFunctionDefinition[Any, Any]]
    """The operations to encode / replace with the given functions. Keys are tuples
    (namespace, name) for the operation to replace."""
    setup: GuppyFunctionDefinition[[], None]
    """Called before the computational program."""
    teardown: GuppyFunctionDefinition[[], None]
    """Called after the computational program."""
    tket_passes: list[ComposablePass]
    """Additional tket passes to run on the computational program."""
    wrapper_extensions: list[Extension] = field(default_factory=list)
    """Extensions required to (de)serialize programs using setup/teardown."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the encoded program."""
