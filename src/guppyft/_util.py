from typing import Any, overload

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
# See https://github.com/Quantinuum/hugr/issues/3193
def extension_registry_to_json(registry: ExtensionRegistry) -> str:
    """Serializes an `ExtensionRegistry` as a JSON array of extensions.

    `ExtensionRegistry` itself has no `to_json`/`__str__` serialization, but each
    contained `Extension` does; this combines them into the list format expected by
    `hugr_core::extension::ExtensionRegistry::load_json` on the Rust side.
    """
    import json

    return json.dumps([json.loads(ext.to_json()) for ext in registry.extensions])


class PathDict[V](dict[str, V]):
    """A dictionary tracking the path to a certain key to provide better error messages
    on required keys."""

    _path: str | None = None

    @property
    def path(self) -> str:
        """The path the dictionary has tracked so far."""
        return self._path or "<root>"

    @overload
    def get(self, key: str, default: None = None, /) -> V | None: ...
    @overload
    def get(self, key: str, default: V, /) -> V: ...
    @overload
    def get[T](self, key: str, default: T, /) -> V | T: ...
    def get[T](self, key: str, default: V | T | None = None, /) -> V | T | None:
        """Return the value for key if key is in the dictionary, else default."""
        value = super().get(key)
        if value is None:
            return default

        if isinstance(value, dict):
            opt = PathDict(value)
            opt._path = f"{self.path}.{key}"
            return opt  # type: ignore[return-value]

        return value

    def __getitem__(self, item: str) -> V:
        """Return self[key]."""
        value = self.get(item)
        if value is None:
            raise KeyError(f"Could not find required key `{item}` at path {self.path}")

        return value
