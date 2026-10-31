import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.library import GuppyLibrary
from tket_exts import quantum

from guppyft._util import get_link_name
from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
    op_replacement_decorator,
)


@pytest.mark.parametrize("as_bytes", [False, True])
def test_default_build_wrapper(as_bytes: bool) -> None:
    @guppy
    def main() -> None:
        pass

    pkg0 = main.compile()
    [module] = pkg0.modules
    entrypoint = module.entrypoint
    before = pkg0.to_str()
    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())

    pkg1 = (
        implement_ops(pkg0, spec, as_bytes=True)
        if as_bytes
        else implement_ops(pkg0, spec)
    )

    assert pkg0.to_str() == before
    [module_after] = pkg0.modules
    assert module_after is module
    assert module.entrypoint == entrypoint

    EmulatorBuilder().build(pkg1, n_qubits=1).run()


def test_op_replacement_decorator() -> None:
    ops = OpReplacements()
    lib = GuppyLibrary(members=[])
    register_op_replacement = op_replacement_decorator(ops, register_in=lib)

    @register_op_replacement(quantum.X.op_def())
    def main() -> None:
        pass

    assert [main.id] == lib.members
    [registered_op] = list(ops.__iter__())
    op, (_, link_name) = registered_op
    assert op == ("tket.quantum", "X")
    assert get_link_name(main) == link_name == "link.tket.quantum.X"
