from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from guppylang_internals.definition.declaration import CheckedFunctionDecl
from guppylang_internals.definition.function import ParsedFunctionDef
from guppylang_internals.engine import ENGINE


def link_name(func: GuppyFunctionDefinition[Any, Any]) -> str:
    match ENGINE.get_parsed(func.id):
        case ParsedFunctionDef(link_name=name):
            return name
        case CheckedFunctionDecl(link_name=name):
            return name
        case _:
            raise ValueError(f"Unknown link name for function with ID {func.id}")
