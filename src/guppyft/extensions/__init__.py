"""HUGR extension definitions for QEC codes."""

from guppyft.extensions import helix, iceberg, std, steane
from guppyft.extensions.helix import HelixOpsExtension, HelixTypesExtension
from guppyft.extensions.iceberg import IcebergOpsExtension, IcebergTypesExtension
from guppyft.extensions.std import StdOpsExtension, StdTypesExtension
from guppyft.extensions.steane import SteaneOpsExtension, SteaneTypesExtension

__all__ = [
    "helix",
    "helix_ops",
    "helix_types",
    "iceberg",
    "iceberg_ops",
    "iceberg_types",
    "std",
    "std_ops",
    "std_types",
    "steane",
    "steane_ops",
    "steane_types",
]

helix_ops: HelixOpsExtension = helix.HelixOpsExtension()
helix_types: HelixTypesExtension = helix.HelixTypesExtension()
iceberg_ops: IcebergOpsExtension = iceberg.IcebergOpsExtension()
iceberg_types: IcebergTypesExtension = iceberg.IcebergTypesExtension()
steane_ops: SteaneOpsExtension = steane.SteaneOpsExtension()
steane_types: SteaneTypesExtension = steane.SteaneTypesExtension()
std_ops: StdOpsExtension = std.StdOpsExtension()
std_types: StdTypesExtension = std.StdTypesExtension()
