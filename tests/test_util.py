from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.library import link_name

from guppyft._util import PathDict, get_link_name


def test_link_name() -> None:
    @guppy
    @no_type_check
    @link_name("custom.link.name")
    def func() -> None:
        return func_decl()

    @guppy.declare
    @no_type_check
    @link_name("custom.link.name.for.decl")
    def func_decl() -> None: ...

    _ = func.compile_function()
    assert get_link_name(func) == "custom.link.name"
    assert get_link_name(func_decl) == "custom.link.name.for.decl"


def test_pathdict_simple() -> None:
    path_dict = PathDict({"a": 1, "b": 2})
    assert path_dict["a"] == 1
    assert path_dict["b"] == 2
    assert path_dict.get("a") == 1
    assert path_dict.get("b") == 2
    assert path_dict.get("c") is None
    assert path_dict.get("c", "default-val") == "default-val"


def test_pathdict_preserves_keys() -> None:
    path_dict = PathDict({"a": 1, "b": 2})
    assert set(path_dict.keys()) == {"a", "b"}


def test_pathdict_returns_path() -> None:
    path_dict = PathDict({"a": 1, "b": {"c": 2}})

    assert path_dict.path == "<root>"
    assert path_dict["b"].path == "<root>.b"  # type: ignore[attr-defined]


def test_pathdict_error() -> None:
    path_dict = PathDict({"a": 1, "b": {"c": 2}})
    with pytest.raises(KeyError, match=r"required key `d` at path <root>"):
        _ = path_dict["d"]


def test_pathdict_nested_error() -> None:
    path_dict = PathDict({"a": 1, "b": {"c": 2}})
    with pytest.raises(KeyError, match=r"required key `d` at path <root>.b"):
        _ = path_dict["b"]["d"]  # type: ignore[index]
