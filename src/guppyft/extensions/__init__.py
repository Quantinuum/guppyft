"""HUGR extension definitions for QEC codes."""

from hugr.ext import ExtensionRegistry

from guppyft.extensions import iceberg, std, steane
from guppyft.extensions.iceberg import IcebergOpsExtension, IcebergTypesExtension
from guppyft.extensions.std import StdOpsExtension, StdTypesExtension
from guppyft.extensions.steane import SteaneOpsExtension, SteaneTypesExtension

__all__ = [
    "iceberg_ops",
    "iceberg_types",
    "std_ops",
    "std_types",
    "steane_ops",
    "steane_types",
]

iceberg_ops: IcebergOpsExtension = iceberg.IcebergOpsExtension()
iceberg_types: IcebergTypesExtension = iceberg.IcebergTypesExtension()
steane_ops: SteaneOpsExtension = steane.SteaneOpsExtension()
steane_types: SteaneTypesExtension = steane.SteaneTypesExtension()
std_ops: StdOpsExtension = std.StdOpsExtension()
std_types: StdTypesExtension = std.StdTypesExtension()

# Resolve all the extensions. This is a temporary patch required to
# cache the extensions for Guppy compilation.
# Relevant issue:
# https://github.com/Quantinuum/hugr/issues/3159
_registry = ExtensionRegistry.from_extensions(
    [
        iceberg_types(),
        iceberg_ops(),
        steane_types(),
        steane_ops(),
        std_types(),
        std_ops(),
    ]
)

for ext in _registry.extensions:
    ext._resolve_used_extensions(_registry)
