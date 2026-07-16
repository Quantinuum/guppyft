from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary
from hugr.ext import ExtensionRegistry
from hugr.std import _std_extensions

from guppyft.code.steane.primitives import cx, decode, h, measure_z, prep_zero, x, z
from guppyft.encode import (
    EncoderSpec,
    ImplementOpsSpec,
    OpReplacements,
    ReplaceEncoder,
    TyReplacements,
)
from guppyft.extensions import std_ops, std_types, steane_ops, steane_types

lib = GuppyLibrary.from_members(prep_zero, measure_z, decode, x, z, h, cx).compile()

ops = OpReplacements().with_generated_decls(
    {
        ("guppyft.steane.ops", "prep_zero"): "guppyft.Steane.prep_zero",
        ("guppyft.steane.ops", "measure_z"): "guppyft.Steane.measure_z",
        ("guppyft.steane.ops", "x"): "guppyft.Steane.x",
        ("guppyft.steane.ops", "z"): "guppyft.Steane.z",
        ("guppyft.steane.ops", "h"): "guppyft.Steane.h",
        ("guppyft.steane.ops", "cx"): "guppyft.Steane.cx",
        ("guppyft.std.ops", "decode"): "guppyft.Steane.decode",
    }
)
tys = TyReplacements().with_types(
    [
        ("guppyft.steane.types", "qubit"),
        ("guppyft.std.types", "logical_measurement"),
    ]
)


def build_wrapper(
    func: GuppyFunctionDefinition[[], None],
) -> GuppyFunctionDefinition[[], None]:
    @guppy
    def wrapper() -> None:
        func()

    return wrapper


ext = ExtensionRegistry.from_extensions(
    [steane_ops(), steane_types(), std_ops(), std_types()]
)
# TODO _std_extensions should not be necessary but seems to be
#  required for borrow_array when (de)serialising.
ext.extend(_std_extensions())

std_encoder = ReplaceEncoder(
    # TODO This should probably use `OpReplacement` or some other dataclass
    op_replacements={
        ("tket.quantum", "QAlloc"): ("guppyft.steane.ops", "prep_zero", []),
        ("tket.quantum", "MeasureFree"): ("guppyft.steane.ops", "measure_z", []),
        ("tket.measurement", "Read"): ("guppyft.std.ops", "decode", [1]),
    },
    extensions=ext,
)


impl_spec = ImplementOpsSpec(ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib])

enc_spec = EncoderSpec(to_logical=std_encoder, implement_spec=impl_spec)
