from hugr.build.dfg import Dfg
from hugr.ops import DFG
from hugr.tys import ExtType

from guppyft.extensions import toy_k2_ops, toy_k2_types


def test_hugr() -> None:
    """Test that we can build a simple hugr out of ToyK2 operations."""
    block_type = toy_k2_types.toy_k2_block()
    assert block_type.type_def.name == "block"
    assert block_type.args == []
    block_op = toy_k2_ops.cx_transversal()
    assert block_op.name() == "guppyft.toy_k2.ops.cx_transversal"
    dfg = Dfg(block_type, block_type)
    node = dfg.add_op(block_op, *dfg.inputs())
    dfg.set_outputs(node)
    h = dfg.hugr
    h_extn_ids = h.used_extensions().ids()
    assert "guppyft.toy_k2.ops" in h_extn_ids
    assert "guppyft.toy_k2.types" in h_extn_ids
    [fndef] = h.children(h.module_root)
    _inp, _out, dfg = h.children(fndef)
    dfg_data = h.get(dfg)
    assert dfg_data is not None
    dfg_op = dfg_data.op
    assert isinstance(dfg_op, DFG)
    dfg_sig = dfg_op.signature
    [in0, in1] = dfg_sig.input
    assert isinstance(in0, ExtType)
    assert in0.type_def.name == "block"
    assert in0.args == []
    assert isinstance(in1, ExtType)
    assert in1.type_def.name == "block"
    assert in1.args == []


def test_exported_extensions() -> None:
    ops_extn = toy_k2_ops()
    types_extn = toy_k2_types()
    assert len(ops_extn.types) == 0
    assert len(types_extn.operations) == 0
    assert types_extn.types == {
        "block": toy_k2_types.toy_k2_block_def,
        "borrowed_block": toy_k2_types.toy_k2_borrowed_block_def,
        "dynamic_qubit": toy_k2_types.toy_k2_dynamic_qubit_def,
        "block_measurement": toy_k2_types.toy_k2_block_measurement_def,
        "qubit_measurement": toy_k2_types.toy_k2_qubit_measurement_def,
    }
    assert len(ops_extn.operations) == 32
    for op_name, op_def in ops_extn.operations.items():
        assert op_def == toy_k2_ops.__getattribute__(f"{op_name}_def")


def test_op_instantiations() -> None:
    ops_extn = toy_k2_ops()
    # No operations take indices
    assert len(ops_extn.operations) == 32
    for op_name in ops_extn.operations:
        assert (
            toy_k2_ops.__getattribute__(op_name)().op_def()
            == ops_extn.operations[op_name]
        )
