from hugr.build.dfg import Dfg
from hugr.ops import DFG
from hugr.std.float import FLOAT_T
from hugr.tys import BoundedNatArg, ExtType

from guppyft.extensions import iceberg_ops, iceberg_types


def test_hugr() -> None:
    """Test that we can build a simple hugr out of Iceberg operations."""
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


def test_exported_extensions() -> None:
    ops_extn = iceberg_ops()
    types_extn = iceberg_types()
    assert len(ops_extn.types) == 0
    assert len(types_extn.operations) == 0
    assert types_extn.types == {"block": iceberg_types.iceberg_block_def}
    assert all(
        op_def == iceberg_ops.__getattribute__(f"{op_name}_def")
        for op_name, op_def in ops_extn.operations.items()
    )


def test_op_instantiations() -> None:
    ops_extn = iceberg_ops()
    # Dynamic ops all just take a block size:
    for op_name, op_def in ops_extn.operations.items():
        if op_name.endswith("_d"):
            assert iceberg_ops.__getattribute__(op_name)(3).op_def() == op_def
    # Other ops that take no indices:
    for op_name in [
        "all_x",
        "all_y",
        "all_z",
        "all_rx",
        "all_ry",
        "all_rz",
        "all_h",
        "cx_transversal",
        "alloc_zero",
        "free",
        "measure_syndrome",
        "measure_all",
    ]:
        assert (
            iceberg_ops.__getattribute__(op_name)(3).op_def()
            == ops_extn.operations[op_name]
        )
    # Ops that take a single index:
    for op_name in [
        "x",
        "z",
        "all_but_one_x",
        "all_but_one_z",
        "x_with_all_but_one_z",
        "z_with_all_but_one_x",
        "fan_out",
        "fan_in",
        "rx",
        "rz",
        "all_but_one_rx",
        "all_but_one_rz",
        "try_measure_one_x",
        "try_measure_one_z",
    ]:
        assert (
            iceberg_ops.__getattribute__(op_name)(3, 1).op_def()
            == ops_extn.operations[op_name]
        )
    # Ops that take two indices:
    for op_name in [
        "xx",
        "yy",
        "zz",
        "xx_phase",
        "yy_phase",
        "zz_phase",
        "cx",
        "swap",
        "zz_phase_between_blocks",
    ]:
        assert (
            iceberg_ops.__getattribute__(op_name)(3, 1, 2).op_def()
            == ops_extn.operations[op_name]
        )
