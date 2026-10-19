"""Checks for producer compatibility of versioned annotation schemas."""

from copy import deepcopy
from typing import Any

from jsonschema import Draft4Validator
from jsonsubschema import isSubschema  # type: ignore[import-untyped]

Schema = dict[str, Any]


def schema_versions(catalog: dict[str, Schema]) -> dict[str, dict[int, Schema]]:
    """Group hand-crafted contracts by architecture and positive major version."""
    result: dict[str, dict[int, Schema]] = {}
    for key, schema in catalog.items():
        name, separator, major = key.rpartition(".v")
        assert separator, f"Invalid schema key: {key}"
        assert name, f"Invalid schema key: {key}"
        assert major.isdecimal(), f"Invalid schema key: {key}"
        version = int(major)
        assert version > 0, f"Invalid schema key: {key}"
        assert major == str(version), f"Invalid schema key: {key}"
        assert schema["properties"]["schema_version"] == {
            "type": "integer",
            "enum": [version],
        }, f"{key}: schema_version must match the catalog key"
        assert "schema_version" in schema.get("required", []), (
            f"{key}: schema_version must be required"
        )
        assert_schema_version(schema, schema)
        result.setdefault(name, {})[version] = schema
    return result


def assert_schema_catalog(
    current: dict[str, Schema], baseline: dict[str, Schema]
) -> None:
    """Allow compatible revisions; require breaking changes for new majors."""
    assert baseline.keys() <= current.keys(), "Do not remove stored schema majors"
    current_versions = schema_versions(current)
    baseline_versions = schema_versions(baseline)
    for name, versions in current_versions.items():
        previous = baseline_versions.get(name, {})
        for version in sorted(versions):
            schema = versions[version]
            if version in previous:
                assert_schema_version(schema, previous[version])
            else:
                assert not previous or version > max(previous), (
                    f"{name}: new majors must be newer than all stored majors"
                )
                older = [major for major in versions if major < version]
                if older:
                    predecessor = max(older)
                    assert_schema_version(
                        schema, previous.get(predecessor, versions[predecessor])
                    )
                else:
                    assert version == 1, f"{name}: initial schema_version must be 1"


def _check_supported(schema: Schema) -> None:
    supported = {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "enum",
        "minimum",
        "maximum",
        "description",
        "title",
        "$schema",
    }
    assert not (unknown := schema.keys() - supported), (
        "Schema compatibility review needed for unsupported keywords: "
        f"{sorted(unknown)}"
    )
    assert isinstance(schema.get("additionalProperties", True), bool), (
        "Schema-valued additionalProperties needs a compatibility review"
    )
    for child in schema.get("properties", {}).values():
        _check_supported(child)


def _consumer_schema(schema: Schema) -> Schema:
    result = deepcopy(schema)
    if result.get("type") == "object":
        result["additionalProperties"] = True
    for name, child in result.get("properties", {}).items():
        result["properties"][name] = _consumer_schema(child)
    return result


def assert_schema_version(current: Schema, baseline: Schema) -> None:
    """Require a version increase exactly when old consumers cannot read new output.

    Consumers ignore unknown object properties. The root schema_version is excluded
    from the inclusion check; nested versions belong to independently checked contracts.
    Only the explicitly supported JSON Schema Draft 4 subset is compared.
    """
    for schema in (current, baseline):
        Draft4Validator.check_schema(schema)
        _check_supported(schema)
    current_version = current["properties"]["schema_version"]["enum"][0]
    baseline_version = baseline["properties"]["schema_version"]["enum"][0]
    for version in (current_version, baseline_version):
        assert type(version) is int, "Expected an integer schema version"
        assert version > 0, "Expected a positive schema version"

    schemas = [deepcopy(current), _consumer_schema(baseline)]
    for schema in schemas:
        del schema["properties"]["schema_version"]
        schema["required"].remove("schema_version")
        if not schema["required"]:
            del schema["required"]
    compatible = isSubschema(*schemas)
    if compatible:
        assert current_version == baseline_version, (
            "Compatible schema change must retain schema_version "
            f"{baseline_version}, received {current_version}"
        )
    else:
        assert current_version > baseline_version, (
            "Breaking schema change must increase schema_version above "
            f"{baseline_version}, received {current_version}"
        )
