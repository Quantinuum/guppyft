"""Version contracts for serialized architecture annotations."""

import json
import os
import shutil
import subprocess
from copy import deepcopy
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest
from hugr import Hugr
from jsonschema import Draft4Validator

from guppyft.code.steane.encode import (
    QECPolicy,
    QECStyle,
    RUSStateFactoryConf,
    SteaneBuilder,
)
from guppyft.encode import annotate_encoding

from .utils.schema import (
    Schema,
    assert_schema_catalog,
    assert_schema_version,
    schema_versions,
)


def object_schema(properties: dict[str, Schema]) -> Schema:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


SCHEMA_PATH = Path("tests/resources/schemas")
ROOT = Path(__file__).resolve().parents[1]
CATALOG: dict[str, Schema] = {
    path.stem: json.loads(path.read_text())
    for path in sorted((ROOT / SCHEMA_PATH).glob("*.json"))
}
VERSIONS = schema_versions(CATALOG)
ENVELOPE = VERSIONS["envelope"][max(VERSIONS["envelope"])]
STEANE = VERSIONS["steane"][max(VERSIONS["steane"])]
EXAMPLE = object_schema(
    {
        "schema_version": {"type": "integer", "enum": [1]},
        "count": {"type": "integer"},
    }
)


def git_schema_catalog(reference: str) -> dict[str, Schema]:
    git = shutil.which("git")
    assert git is not None, "Schema history checks require Git"
    assert not reference.startswith("-"), "Expected a Git reference, not an option"
    tracked = subprocess.run(  # noqa: S603
        [git, "ls-tree", "-r", "--name-only", reference, "--", SCHEMA_PATH.as_posix()],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    baseline: dict[str, Schema] = {}
    for filename in tracked:
        path = Path(filename)
        if path.parent != SCHEMA_PATH or path.suffix != ".json":
            continue
        schema = json.loads(
            subprocess.run(  # noqa: S603
                [git, "show", f"{reference}:{path.as_posix()}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        )
        if path.name == "baseline.json":
            baseline.update(schema)
        else:
            baseline[path.stem] = schema
    return baseline


def test_annotation_schema_history() -> None:
    reference = os.environ.get("GUPPYFT_SCHEMA_BASE_REF", "HEAD")
    baseline = git_schema_catalog(reference)
    assert_schema_catalog(CATALOG, baseline)


@pytest.mark.parametrize(
    "legacy", [False, True], ids=["separate-files", "legacy-catalog"]
)
def test_git_schema_catalog(monkeypatch: pytest.MonkeyPatch, legacy: bool) -> None:
    filename = SCHEMA_PATH / ("baseline.json" if legacy else "example.v1.json")
    content = {"example.v1": EXAMPLE} if legacy else EXAMPLE

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if command[1] == "ls-tree":
            output = f"{filename.as_posix()}\n{SCHEMA_PATH}/README.md\n"
        else:
            assert command[1:] == ["show", f"test-ref:{filename.as_posix()}"]
            output = json.dumps(content)
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(shutil, "which", lambda executable: "/usr/bin/git")
    monkeypatch.setattr(subprocess, "run", run)
    assert git_schema_catalog("test-ref") == {"example.v1": EXAMPLE}


def test_envelope_serialization_contract() -> None:
    hugr = Hugr[Any]()
    annotate_encoding(
        hugr, "custom-architecture", {"schema_version": 42, "custom": True}
    )
    payload = json.loads(
        json.dumps(hugr[hugr.module_root].metadata["qnt.nexus.compilation"])
    )
    Draft4Validator(ENVELOPE).validate(payload)
    assert payload["ft_encoding"]["params"]["schema_version"] == 42


@pytest.mark.parametrize("style", list(QECStyle))
@pytest.mark.parametrize("configured", [False, True], ids=["defaults", "configured"])
def test_steane_serialization_contract(style: QECStyle, configured: bool) -> None:
    policy = QECPolicy(style=style, threshold=7 if configured else 1)
    if configured:
        for index, cost in enumerate(fields(policy.costs), start=1):
            setattr(policy.costs, cost.name, index + 0.25)
    zero = RUSStateFactoryConf(2, 3) if configured else RUSStateFactoryConf(1, 5)
    magic = RUSStateFactoryConf(4, 6) if configured else RUSStateFactoryConf(1, 5)
    n_blocks = 8 if configured else 4
    instance = (
        SteaneBuilder()
        .with_qec_policy(policy)
        .with_zero_factory_conf(zero)
        .with_magic_factory_conf(magic)
        .build(n_blocks=n_blocks)
    )
    hugr = Hugr[Any]()
    instance.annotate(hugr)
    payload = json.loads(
        json.dumps(hugr[hugr.module_root].metadata["qnt.nexus.compilation"])
    )
    Draft4Validator(ENVELOPE).validate(payload)
    assert payload["ft_encoding"]["name"] == "steane"
    params = payload["ft_encoding"]["params"]
    Draft4Validator(STEANE).validate(params)
    assert params["n_blocks"] == n_blocks
    assert params["zero_factory"] == {
        "size": zero.size,
        "max_attempts": zero.max_attempts,
    }
    assert params["magic_factory"] == {
        "size": magic.size,
        "max_attempts": magic.max_attempts,
    }
    assert params["qec_policy"] == {
        "style": style.value,
        "threshold": policy.threshold,
        "costs": {
            cost.name: getattr(policy.costs, cost.name) for cost in fields(policy.costs)
        },
    }


@pytest.mark.parametrize("version", [1, 2, 0])
@pytest.mark.parametrize(
    ("change", "breaking"),
    [
        ("unchanged", False),
        ("add", False),
        ("nested_add", False),
        ("remove", True),
        ("rename", True),
        ("type", True),
        ("enum_expand", True),
        ("enum_narrow", False),
        ("nullable", True),
        ("optional", True),
        ("reorder", False),
    ],
)
def test_schema_version_guard(change: str, breaking: bool, version: int) -> None:
    baseline = object_schema(
        {
            "schema_version": {"type": "integer", "enum": [1]},
            "nested": object_schema({"style": {"type": "string", "enum": ["a", "b"]}}),
        }
    )
    current = deepcopy(baseline)
    current["properties"]["schema_version"]["enum"] = [version]
    nested = current["properties"]["nested"]
    match change:
        case "add":
            current["properties"]["extra"] = {"type": "integer"}
            current["required"].append("extra")
        case "nested_add":
            nested["properties"]["extra"] = {"type": "integer"}
            nested["required"].append("extra")
        case "remove":
            del nested["properties"]["style"]
            del nested["required"]
        case "rename":
            nested["properties"]["renamed"] = nested["properties"].pop("style")
            nested["required"] = ["renamed"]
        case "type":
            nested["properties"]["style"] = {"type": "integer"}
        case "enum_expand":
            nested["properties"]["style"]["enum"].append("c")
        case "enum_narrow":
            nested["properties"]["style"]["enum"] = ["a"]
        case "nullable":
            nested["properties"]["style"] = {"type": ["string", "null"]}
        case "optional":
            del nested["required"]
        case "reorder":
            current["required"].reverse()
            current["properties"] = dict(reversed(current["properties"].items()))
    if version == 0 or (breaking and version == 1) or (not breaking and version == 2):
        with pytest.raises(AssertionError):
            assert_schema_version(current, baseline)
    else:
        assert_schema_version(current, baseline)


def test_schema_guard_requires_review_for_unsupported_keywords() -> None:
    current = deepcopy(EXAMPLE)
    current["properties"]["count"]["multipleOf"] = 2
    with pytest.raises(AssertionError, match=r"unsupported keywords.*multipleOf"):
        assert_schema_version(current, EXAMPLE)


def test_parameter_version_independent_of_envelope() -> None:
    current = deepcopy(EXAMPLE)
    current["properties"]["schema_version"]["enum"] = [2]
    current["properties"]["count"] = {"type": "string"}
    assert_schema_version(current, EXAMPLE)
    assert_schema_version(ENVELOPE, ENVELOPE)


@pytest.mark.parametrize("breaking", [False, True])
def test_schema_version_cannot_decrease(breaking: bool) -> None:
    baseline = deepcopy(EXAMPLE)
    baseline["properties"]["schema_version"]["enum"] = [2]
    current = deepcopy(EXAMPLE)
    if breaking:
        current["properties"]["count"] = {"type": "string"}
    with pytest.raises(AssertionError, match="schema_version"):
        assert_schema_version(current, baseline)


@pytest.mark.parametrize("breaking", [False, True])
@pytest.mark.parametrize("new_major", [False, True])
def test_catalog_revision_policy(breaking: bool, new_major: bool) -> None:
    original = object_schema(
        {
            "schema_version": {"type": "integer", "enum": [1]},
            "count": {"type": "integer"},
        }
    )
    baseline = {"example.v1": original}
    current = deepcopy(baseline)
    revised = deepcopy(original)
    if breaking:
        revised["properties"]["count"] = {"type": "string"}
    else:
        revised["properties"]["extra"] = {"type": "integer"}
        revised["required"].append("extra")
    if new_major:
        revised["properties"]["schema_version"]["enum"] = [2]
    current[f"example.v{2 if new_major else 1}"] = revised
    if breaking != new_major:
        with pytest.raises(AssertionError, match="schema_version"):
            assert_schema_catalog(current, baseline)
    else:
        assert_schema_catalog(current, baseline)


def test_catalog_preserves_older_majors() -> None:
    with pytest.raises(AssertionError, match="Do not remove"):
        assert_schema_catalog({}, CATALOG)


def test_catalog_key_matches_payload_version() -> None:
    with pytest.raises(AssertionError, match="must match"):
        schema_versions({"example.v2": EXAMPLE})


def test_catalog_selects_latest_major_numerically() -> None:
    catalog = {}
    for version in (2, 10, 1):
        schema = deepcopy(EXAMPLE)
        schema["properties"]["schema_version"]["enum"] = [version]
        catalog[f"example.v{version}"] = schema
    assert max(schema_versions(catalog)["example"]) == 10
