from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder
from guppylang.library import GuppyLibrary
from guppylang.std.platform import result

from guppyft.code.steane.primitives import measure_z, prep_zero
from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)
from guppyft.logical import steane as steane_logical

lib = GuppyLibrary.from_members(prep_zero, measure_z).compile()

ops = OpReplacements().with_generated_decls(
    {
        ("guppyft.steane.ops", "prep_zero"): "guppyft.Steane.prep_zero",
        ("guppyft.steane.ops", "measure_z"): "guppyft.Steane.measure_z",
    }
)
tys = TyReplacements().with_types([("guppyft.steane.types", "qubit")])


def build_wrapper(
    func: GuppyFunctionDefinition[[], None],
) -> GuppyFunctionDefinition[[], None]:
    @guppy
    def wrapper() -> None:
        func()

    return wrapper


spec = ImplementOpsSpec(ops=ops, tys=tys, build_wrapper=build_wrapper, libs=[lib])


def test_qalloc_measure() -> None:

    @guppy
    def main() -> None:
        q = steane_logical.Qubit()
        result("res", steane_logical.measure_z(q))

    pkg = main.compile()

    implemented_pkg = implement_ops(pkg, spec)
    res = EmulatorBuilder().build(implemented_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [0]}]
