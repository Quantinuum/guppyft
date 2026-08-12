"""Utility functions for QEC extensions."""

import functools
import pkgutil
from collections.abc import Sequence

from hugr.ext import Extension, ExtensionRegistry


@functools.cache
def load_extension_json(name: str) -> str:
    from guppyft import extensions

    replacement = name.replace(".", "/")
    json_str = pkgutil.get_data(extensions.__name__, f"data/{replacement}.json")
    assert json_str is not None, f"Could not load json for extension {name}"
    return json_str.decode()


def load_extension(name: str, dependencies: Sequence[str] | None = None) -> Extension:
    if dependencies is None:
        dependencies = []

    registry = ExtensionRegistry.from_extensions(
        [Extension.from_json(load_extension_json(dep)) for dep in dependencies]
    )

    return Extension.from_json(load_extension_json(name), registry)
