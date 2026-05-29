"""HUGR extension definitions for QEC codes."""

from guppyft.extensions import iceberg
from guppyft.extensions.iceberg import IcebergOpsExtension, IcebergTypesExtension

__all__ = ["iceberg_ops", "iceberg_types"]

iceberg_ops: IcebergOpsExtension = iceberg.IcebergOpsExtension()
iceberg_types: IcebergTypesExtension = iceberg.IcebergTypesExtension()
