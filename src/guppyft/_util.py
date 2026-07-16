from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from guppylang_internals.definition.declaration import CheckedFunctionDecl
from guppylang_internals.definition.function import ParsedFunctionDef
from guppylang_internals.engine import ENGINE
from hugr.ext import ExtensionRegistry


# TODO this should eventually be moved to guppylang and made generally available
# See: https://github.com/Quantinuum/guppylang/issues/1697
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


# TODO This should be part of ExtensionRegistry definition in hugr-py
def extension_registry_to_json(registry: ExtensionRegistry) -> str:
    """Serializes an `ExtensionRegistry` as a JSON array of extensions.

    `ExtensionRegistry` itself has no `to_json`/`__str__` serialization, but each
    contained `Extension` does; this combines them into the list format expected by
    `hugr_core::extension::ExtensionRegistry::load_json` on the Rust side.
    """
    import json

    return json.dumps([json.loads(ext.to_json()) for ext in registry.extensions])
