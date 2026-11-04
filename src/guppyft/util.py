"""General utilities for use in QEC architectures and beyond."""

from typing import overload


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
