"""Utility functions for QEC extensions."""

import pkgutil

from hugr.ext import Extension
from semver import Version


def load_extension(name: str, version: Version) -> Extension:
    from guppyft import extensions

    replacement = name.replace(".", "/")
    json_str = pkgutil.get_data(
        extensions.__name__, f"data/{replacement}-{version}.json"
    )
    assert json_str is not None, f"Could not load json for extension {name}"
    return Extension.from_json(json_str.decode())
