from guppylang import guppy
from guppylang.emulator import EmulatorBuilder

from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)


def test_default_build_wrapper() -> None:
    @guppy
    def main() -> None:
        pass

    pkg0 = main.compile()
    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())

    pkg1 = implement_ops(pkg0, spec)

    EmulatorBuilder().build(pkg1, n_qubits=1).run()
