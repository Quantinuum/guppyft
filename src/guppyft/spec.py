from dataclasses import dataclass, field
from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr.ext import Extension
from hugr.package import Package
from hugr.passes.composable import ComposablePass


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    ops: dict[tuple[str, str], GuppyFunctionDefinition[Any, Any]]
    """The operations to encode / replace with the given functions. Keys are tuples
    (namespace, name) for the operation to replace."""
    setup: GuppyFunctionDefinition[[], None]
    """Called before the unencoded program."""
    teardown: GuppyFunctionDefinition[[], None]
    """Called after the unencoded program."""
    tket_passes: list[ComposablePass]
    """Additional tket passes to run on the unencoded program."""
    lifecycle_extensions: list[Extension] = field(default_factory=list)
    """Extensions required to (de)serialize programs using setup/teardown."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the encoded program."""
