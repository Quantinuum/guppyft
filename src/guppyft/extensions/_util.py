"""Utility functions for QEC extensions."""

import pkgutil

from hugr.ext import Extension


def load_extension(name: str) -> Extension:
    from guppyft import extensions

    replacement = name.replace(".", "/")
    json_str = pkgutil.get_data(extensions.__name__, f"data/{replacement}.json")
    assert json_str is not None, f"Could not load json for extension {name}"
    return Extension.from_json(json_str.decode())
