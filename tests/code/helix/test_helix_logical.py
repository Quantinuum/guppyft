"""Compile Helix logical programs and validate the emitted HUGRs."""

import pytest
from guppylang import guppy
from hugr.cli import validate
from hugr.ops import ExtOp
from tket.passes import InlineFunctions, Normalize

from guppyft.code.helix.logical import (
    Block,
    TState,
    alloc_plus,
    alloc_zero,
    cx_between_blocks,
    cx_transversal,
    free_t_state,
    inject_t,
    inject_tdg,
    prep_t_state,
)
from guppyft.extensions import helix_ops


def test_block_operations() -> None:
    @guppy
    def main() -> None:
        a = Block()
        b = alloc_plus()
        a.x(0)
        a.y(1)
        a.z(0)
        a.swap()
        a.cx()
        a.h_all()
        a.cz()
        a.ss()
        a.qec_cycle()
        cx_between_blocks(a, b, 0, 1)
        cx_transversal(a, b)
        inject_t(a, 0, prep_t_state())
        inject_tdg(a, 1, TState())
        a.t(0)
        a.tdg(1)
        a.measure_xx().decode()
        b.measure_zz().decode()
        alloc_zero().free()
        TState().free()
        free_t_state(prep_t_state())

    h = main.compile().modules[0]
    validate(h.to_bytes())
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    validate(h.to_bytes())
    assert not h.used_extensions().unresolved_extensions
    operations = {
        data.op.op_def().name
        for _, data in h.nodes()
        if isinstance(data.op, ExtOp)
        and data.op.op_def().get_extension().name == helix_ops().name
    }
    assert operations == set(helix_ops().operations)


def test_injection_consumes_magic_resource() -> None:
    from guppylang_internals.error import GuppyError

    @guppy
    def main() -> None:
        block = Block()
        magic = TState()
        inject_t(block, 0, magic)
        free_t_state(magic)
        block.free()

    with pytest.raises(GuppyError):
        main.compile()
