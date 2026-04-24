from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr.package import Package
from hugr.passes.composable import ComposablePass


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    ops: dict[tuple[str, str], GuppyFunctionDefinition[Any, Any]]
    """The operations to encode / replace with the given functions. Keys are tuples
    (namespace, name) for the operation to replace."""
    build_wrapper: Callable[
        [GuppyFunctionDefinition[[], None]], GuppyFunctionDefinition[[], None]
    ] = field(default=lambda x: x)
    """Allows creating a wrapper around the encoded program, e.g. to setup and teardown
    the required environment."""
    tket_passes: list[ComposablePass] = field(default_factory=list)
    """Additional tket passes to run on the unencoded program."""
    libs: list[Package] = field(default_factory=list)
    """Additional libraries required to run the encoded program."""
