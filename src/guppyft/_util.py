from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from guppylang_internals.definition.declaration import CheckedFunctionDecl
from guppylang_internals.definition.function import ParsedFunctionDef
from guppylang_internals.engine import ENGINE


# TODO this should eventually be moved to guppylang and made generally available
def get_link_name(func: GuppyFunctionDefinition[Any, Any]) -> str:
    """Extracts the link name from a function, if possible (i.e. if the function is a
    definition or a declaration)."""
    match ENGINE.get_parsed(func.id):
        case ParsedFunctionDef(link_name=name):
            return name
        case CheckedFunctionDecl(link_name=name):
            return name
        case _:
            raise ValueError(f"Unknown link name for function with ID {func.id}")
