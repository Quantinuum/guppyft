import pytest

from guppyft.util import PathDict


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
