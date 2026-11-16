from typing import TYPE_CHECKING

import pytest
from guppylang import guppy, qubit
from guppylang.emulator import EmulatorBuilder
from guppylang.std.quantum import discard
from hugr.ops import ExtOp

from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)

if TYPE_CHECKING:
    from hugr.package import Package


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


def test_preserves_packaged_extensions_for_opaque_ops() -> None:
    """Regression test for implementing ops on a hugr with opaque ops where the
    extensions are packaged but not resolved."""

    @guppy
    def main() -> None:
        discard(qubit())

    pkg1: Package = main.compile()

    [hugr] = pkg1.modules
    for node_data in hugr.values():
        if isinstance(node_data.op, ExtOp):
            node_data.op = node_data.op.to_custom_op()  # Make all ops opaque

    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())
    pkg2 = implement_ops(pkg1, spec)

    assert {e.name for e in pkg1.extensions}.issubset({e.name for e in pkg2.extensions})
