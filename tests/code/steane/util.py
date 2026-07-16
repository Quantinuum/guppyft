from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary

from guppyft.code.steane.primitives import cx, decode, h, measure_z, prep_zero, x, z
from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
)

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


steane_spec = ImplementOpsSpec(
    ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib]
)
