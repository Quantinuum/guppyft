"""GuppyFT standard code extension."""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import BoundedNatArg, ExtType

from guppyft.extensions._util import load_extension


class StdTypesExtension:
    """Extension providing standard logical types."""

    def __call__(self) -> Extension:
        """Returns the standard types extension."""
        return load_extension("guppyft.std.types")

    @functools.cached_property
    def logical_measurement_def(self) -> TypeDef:
        """A logical measurement.

        This is the generic type definition. For the instantiated type, see
        `logical_measurement`.
        """
        return self().get_type("logical_measurement")

    def logical_measurement(self, k: int) -> ExtType:
        """A logical measurement.

        Args:
            k: The number of logical measurements.
        """
        return self.logical_measurement_def.instantiate([BoundedNatArg(k)])


class StdOpsExtension:
    """Extension providing standard logical operations."""

    def __call__(self) -> Extension:
        """Returns the standard ops extension."""
        return load_extension("guppyft.std.ops")

    @functools.cached_property
    def decode_def(self) -> OpDef:
        """Decode a logical measurement.

        This is the generic type definition. For the instantiated type, see
        `decode`.
        """
        return self().get_op("decode")

    def decode(self, k: int) -> ExtOp:
        """Decode a logical measurement.

        Args:
            k: The number of logical measurements.
        """
        return self.decode_def.instantiate([BoundedNatArg(k)])
