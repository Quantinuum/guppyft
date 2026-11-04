"""Tests for the Python bindings of the Helix HUGR extensions."""

import pytest
from hugr.build.dfg import Dfg
from hugr.cli import validate
from hugr.std.int import int_t
from hugr.tys import FunctionType, TypeBound

from guppyft.extensions import helix, helix_ops, helix_types, std_types


def test_exported_extensions() -> None:
    assert isinstance(helix_ops, helix.HelixOpsExtension)
    assert isinstance(helix_types, helix.HelixTypesExtension)
    types_extension = helix_types()
    assert set(types_extension.types) == {"block", "t_state"}
    assert not types_extension.operations
    assert len(helix_ops().operations) == 20
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
    op = getattr(helix_ops, name)()
    assert op.op_def() == definition
    assert op.args == []
    signature = op.outer_signature()
    dfg = Dfg(*signature.input)
    node = dfg.add_op(op, *dfg.inputs())
    dfg.set_outputs(*(node.out(i) for i in range(len(signature.output))))
    validate(dfg.hugr.to_bytes())


def test_magic_state_signatures() -> None:
    block = helix_types.helix_block()
    resource = helix_types.helix_t_state()
    for name in ["inject_t", "inject_tdg"]:
        assert getattr(helix_ops, name)().outer_signature() == FunctionType(
            [block, int_t(6), resource], [block]
        )
    for name in ["measure_x_all", "measure_z_all"]:
        assert getattr(helix_ops, name)().outer_signature() == FunctionType(
            [block], [std_types.logical_measurement(2)]
        )


def test_inject_measure() -> None:
    dfg = Dfg(helix_types.helix_block(), int_t(6))
    block, index = dfg.inputs()
    resource = dfg.add_op(helix_ops.prep_t_state())
    injected = dfg.add_op(helix_ops.inject_t(), block, index, resource)
    resource = dfg.add_op(helix_ops.prep_t_state())
    injected = dfg.add_op(helix_ops.inject_tdg(), injected, index, resource)
    measured = dfg.add_op(helix_ops.measure_z_all(), injected)
    dfg.set_outputs(measured)
    validate(dfg.hugr.to_bytes())
