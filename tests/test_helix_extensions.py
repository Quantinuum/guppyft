"""Tests for the Python bindings of the Helix HUGR extensions."""

import pytest
from hugr.build.dfg import Dfg
from hugr.cli import validate
from hugr.std.int import int_t
from hugr.tys import BoundedNatArg, FunctionType, TypeBound

from guppyft.extensions import helix, helix_ops, helix_types, std_types

_BORROW_RESTORE = {"borrow", "borrow_more", "restore_some", "restore"}


def test_exported_extensions() -> None:
    assert isinstance(helix_ops, helix.HelixOpsExtension)
    assert isinstance(helix_types, helix.HelixTypesExtension)
    types_extension = helix_types()
    assert set(types_extension.types) == {"block", "borrowed_block", "qubit", "t_state"}
    assert not types_extension.operations
    assert len(helix_ops().operations) == 39
    assert not helix_ops().types
    for name, definition in types_extension.types.items():
        assert getattr(helix_types, f"helix_{name}_def") == definition
        ty = getattr(helix_types, f"helix_{name}")()
        assert ty.type_def == definition
        assert ty.args == []
        assert ty.type_bound() == TypeBound.Linear


@pytest.mark.parametrize("name", sorted(helix_ops().operations))
def test_operations(name: str) -> None:
    definition = getattr(helix_ops, f"{name}_def")
    assert definition == helix_ops().get_op(name)
    method = getattr(helix_ops, name)
    op = method(2) if name in _BORROW_RESTORE else method()
    assert op.op_def() == definition
    assert op.args == ([BoundedNatArg(2)] if name in _BORROW_RESTORE else [])
    # Serialize every operation in a complete graph and validate using Rust.
    signature = op.outer_signature()
    dfg = Dfg(*signature.input)
    node = dfg.add_op(op, *dfg.inputs())
    dfg.set_outputs(*(node.out(i) for i in range(len(signature.output))))
    validate(dfg.hugr.to_bytes())


@pytest.mark.parametrize("name", sorted(_BORROW_RESTORE))
@pytest.mark.parametrize("m", [0, 1, 2])
def test_borrow_restore_signatures(name: str, m: int) -> None:
    block = helix_types.helix_block()
    borrowed = helix_types.helix_borrowed_block()
    qubit = helix_types.helix_qubit()
    match name:
        case "borrow":
            expected = FunctionType(
                [block, *([int_t(6)] * m)], [borrowed, *([qubit] * m)]
            )
        case "borrow_more":
            expected = FunctionType(
                [borrowed, *([int_t(6)] * m)], [borrowed, *([qubit] * m)]
            )
        case "restore_some":
            expected = FunctionType([borrowed, *([qubit] * m)], [borrowed])
        case "restore":
            expected = FunctionType([borrowed, *([qubit] * m)], [block])
        case _:
            raise AssertionError(name)
    assert getattr(helix_ops, name)(m).outer_signature() == expected


@pytest.mark.parametrize("name", sorted(_BORROW_RESTORE))
@pytest.mark.parametrize("m", [-1, 3, 100])
def test_invalid_counts(name: str, m: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 2"):
        getattr(helix_ops, name)(m)


def test_magic_state_signatures() -> None:
    block = helix_types.helix_block()
    qubit = helix_types.helix_qubit()
    resource = helix_types.helix_t_state()
    for name in ["inject_t", "inject_tdg"]:
        assert getattr(helix_ops, name)().outer_signature() == FunctionType(
            [block, int_t(6), resource], [block]
        )
    for name in ["inject_t_dynq", "inject_tdg_dynq"]:
        assert getattr(helix_ops, name)().outer_signature() == FunctionType(
            [qubit, resource], [qubit]
        )
    assert helix_ops.measure_z_dynq().outer_signature() == FunctionType(
        [qubit], [std_types.logical_measurement(1)]
    )


def test_borrow_inject_restore_measure() -> None:
    dfg = Dfg(helix_types.helix_block(), int_t(6), int_t(6))
    block, zero, one = dfg.inputs()
    first = dfg.add_op(helix_ops.borrow(1), block, zero)
    second = dfg.add_op(helix_ops.borrow_more(1), first.out(0), one)
    pair = dfg.add_op(helix_ops.cx_dynq(), first.out(1), second.out(1))
    resource = dfg.add_op(helix_ops.prep_t_state())
    injected = dfg.add_op(helix_ops.inject_t_dynq(), pair.out(0), resource)
    owner = dfg.add_op(helix_ops.restore_some(1), second.out(0), pair.out(1))
    restored = dfg.add_op(helix_ops.restore(1), owner, injected)
    measured = dfg.add_op(helix_ops.measure_zz(), restored)
    dfg.set_outputs(measured)
    validate(dfg.hugr.to_bytes())
