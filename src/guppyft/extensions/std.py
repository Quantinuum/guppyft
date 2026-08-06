"""guppyft.std code extension"""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import BoundedNatArg, ExtType

from guppyft.extensions._util import load_extension


class StdTypesExtension:
    def __call__(self) -> Extension:
        return load_extension("guppyft.std.types")

    @functools.cached_property
    def logical_measurement_def(self) -> TypeDef:
        return self().get_type("logical_measurement")

    def logical_measurement(self, k: int) -> ExtType:
        return self.logical_measurement_def.instantiate([BoundedNatArg(k)])


class StdOpsExtension:
    def __call__(self) -> Extension:
        return load_extension("guppyft.std.ops")

    @functools.cached_property
    def decode_def(self) -> OpDef:
        return self().get_op("decode")

    def decode(self, k: int) -> ExtOp:
        return self.decode_def.instantiate([BoundedNatArg(k)])
