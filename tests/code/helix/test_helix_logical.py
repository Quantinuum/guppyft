"""Compile Helix logical programs and validate the emitted HUGRs."""

import pytest
from guppylang import guppy
from guppylang.std.builtins import array, result
from hugr.cli import validate
from hugr.ops import ExtOp
from hugr.tys import BoundedNatArg
from tket.passes import InlineFunctions, Normalize

from guppyft.code.helix.logical import (
    Block,
    Qubit,
    TState,
    alloc_dynq,
    alloc_plus,
    alloc_zero,
    borrow,
    cx_between_blocks,
    cx_dynq,
    cx_transversal,
    cz_dynq,
    free_t_state,
    inject_t,
    inject_t_dynq,
    inject_tdg,
    inject_tdg_dynq,
    prep_t_state,
    restore,
    swap_dynq,
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
        a.cx_swap()
        a.hh_swap()
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


def test_dynamic_operations() -> None:
    @guppy
    def main() -> None:
        a = Qubit()
        b = alloc_dynq()
        a.x()
        a.y()
        a.z()
        a.h()
        a.s()
        a.sdg()
        cx_dynq(a, b)
        cz_dynq(a, b)
        swap_dynq(a, b)
        inject_t_dynq(a, prep_t_state())
        inject_tdg_dynq(b, TState())
        a.t()
        b.tdg()
        mx = a.measure_x().decode()
        mz = b.measure_z().decode()
        result("x", mx[0])
        result("z", mz[0])
        Qubit().free()

    h = main.compile().modules[0]
    validate(h.to_bytes())
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    validate(h.to_bytes())
    assert not h.used_extensions().unresolved_extensions


def test_borrow_restore() -> None:
    @guppy
    def main() -> None:
        b = Block()
        owner, first = b.borrow(array(0))
        second = owner.borrow_more(array(1))
        cx_dynq(first[0], second[0])
        first[0].t()
        owner.restore_some(second)
        b = owner.restore(first)
        owner, qubits = borrow(b, array(1, 0))
        qubits[0].h()
        qubits[1].z()
        b = restore(owner, qubits)
        b.qec_cycle()
        b.free()

    h = main.compile().modules[0]
    validate(h.to_bytes())
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    validate(h.to_bytes())
    borrow_ops = [
        data.op
        for _, data in h.nodes()
        if isinstance(data.op, ExtOp)
        and data.op.op_def().name
        in {"borrow", "borrow_more", "restore_some", "restore"}
        and data.op.op_def().get_extension().name == helix_ops().name
    ]
    assert {op.op_def().name for op in borrow_ops} == {
        "borrow",
        "borrow_more",
        "restore_some",
        "restore",
    }
    for op in borrow_ops:
        [count] = op.args
        assert isinstance(count, BoundedNatArg)
        assert count.n in {1, 2}
        assert (
            op.outer_signature()
            == getattr(helix_ops, op.op_def().name)(count.n).outer_signature()
        )
    assert not h.used_extensions().unresolved_extensions


def test_zero_length_borrow_restore() -> None:
    @guppy
    def main() -> None:
        indices: array[int, 0] = array()
        owner, empty = borrow(Block(), indices)
        more = owner.borrow_more(indices)
        owner.restore_some(more)
        b = restore(owner, empty)
        b.free()

    h = main.compile().modules[0]
    validate(h.to_bytes())
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    validate(h.to_bytes())


def test_borrow_rejects_excessive_count() -> None:
    @guppy
    def main() -> None:
        owner, qubits = borrow(Block(), array(0, 1, 0))
        restore(owner, qubits).free()

    with pytest.raises(ValueError, match="between 0 and 2"):
        main.compile()


def test_injection_consumes_magic_resource() -> None:
    from guppylang_internals.error import GuppyError

    @guppy
    def main() -> None:
        q = Qubit()
        magic = TState()
        inject_t_dynq(q, magic)
        free_t_state(magic)
        q.free()

    with pytest.raises(GuppyError):
        main.compile()


def test_borrow_consumes_original_block() -> None:
    from guppylang_internals.error import GuppyError

    @guppy
    def main() -> None:
        b = Block()
        owner, qubits = borrow(b, array(0))
        b.qec_cycle()
        restore(owner, qubits).free()

    with pytest.raises(GuppyError):
        main.compile()
