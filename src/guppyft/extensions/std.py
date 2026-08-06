"""guppyft.std code extension"""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import Bool, BoundedNatArg, ExtType, ListArg, TypeTypeArg

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
        # `decode` takes both `k` (the receiver's size) and an explicit row
        # of `k` `Bool` types (substituted into the tuple output's row
        # variable) -- see `extensions/src/std/ops.rs` for why the tuple's
        # arity can't be derived from `k` alone within the op's signature.
        return self.decode_def.instantiate(
            [BoundedNatArg(k), ListArg([TypeTypeArg(Bool)] * k)]
        )
