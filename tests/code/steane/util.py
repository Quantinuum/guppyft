from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.library import GuppyLibrary

from guppyft.code.steane.primitives import decode, measure_z, prep_zero
from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
)

lib = GuppyLibrary.from_members(prep_zero, measure_z, decode).compile()

ops = OpReplacements().with_generated_decls(
    {
        ("guppyft.steane.ops", "prep_zero"): "guppyft.Steane.prep_zero",
        ("guppyft.steane.ops", "measure_z"): "guppyft.Steane.measure_z",
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


steane_spec = ImplementOpsSpec(ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib])
