import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorBuilder

from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)


@pytest.mark.parametrize("as_bytes", [False, True])
def test_default_build_wrapper(as_bytes: bool) -> None:
    @guppy
    def main() -> None:
        pass

    pkg0 = main.compile()
    module = pkg0.modules[0]
    entrypoint = module.entrypoint
    before = pkg0.to_str()
    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())

    pkg1 = (
        implement_ops(pkg0, spec, as_bytes=True)
        if as_bytes
        else implement_ops(pkg0, spec)
    )

    assert pkg0.modules[0] is module
    assert module.entrypoint == entrypoint
    assert pkg0.to_str() == before

    EmulatorBuilder().build(pkg1, n_qubits=1).run()
