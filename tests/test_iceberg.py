from hugr.build.dfg import Dfg
from hugr.ops import DFG
from hugr.std.float import FLOAT_T
from hugr.tys import BoundedNatArg, ExtType

from guppyft.extensions import iceberg_ops, iceberg_types


def test_hugr() -> None:
    block6type = iceberg_types.iceberg_block(6)
    assert block6type.type_def.name == "block"
    assert block6type.args == [BoundedNatArg(6)]
    block6op = iceberg_ops.all_but_one_rx(6, 2)
    assert block6op.name() == "guppyft.iceberg.ops.all_but_one_rx<6, 2>"
    dfg = Dfg(block6type, FLOAT_T)
    node = dfg.add_op(block6op, *dfg.inputs())
    dfg.set_outputs(node)
    h = dfg.hugr
    h_extn_ids = h.used_extensions().ids()
    assert "guppyft.iceberg.ops" in h_extn_ids
    assert "guppyft.iceberg.types" in h_extn_ids
    [fndef] = h.children(h.module_root)
    _inp, _out, dfg = h.children(fndef)
    dfg_data = h.get(dfg)
    assert dfg_data is not None
    dfg_op = dfg_data.op
    assert isinstance(dfg_op, DFG)
    dfg_sig = dfg_op.signature
    [in0, in1] = dfg_sig.input
    assert isinstance(in0, ExtType)
    assert isinstance(in1, ExtType)
    assert in0.type_def.name == "block"
    assert in0.args == [BoundedNatArg(6)]
    assert in1.type_def.name == "float64"
