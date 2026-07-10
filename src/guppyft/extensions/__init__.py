"""HUGR extension definitions for QEC codes."""

from guppyft.extensions import iceberg, steane
from guppyft.extensions.iceberg import IcebergOpsExtension, IcebergTypesExtension
from guppyft.extensions.steane import SteaneOpsExtension, SteaneTypesExtension

__all__ = [
    "iceberg_ops",
    "iceberg_types",
    "steane_ops",
    "steane_types",
]

iceberg_ops: IcebergOpsExtension = iceberg.IcebergOpsExtension()
iceberg_types: IcebergTypesExtension = iceberg.IcebergTypesExtension()
steane_ops: SteaneOpsExtension = steane.SteaneOpsExtension()
steane_types: SteaneTypesExtension = steane.SteaneTypesExtension()
