from guppylang import guppy
from guppylang.std.builtins import array, result
from hugr.build.dfg import Dfg
from hugr.ops import DFG, ExtOp
from hugr.std.float import FLOAT_T
from hugr.tys import BoundedNatArg, ExtType
from tket.passes import InlineFunctions, Normalize

from guppyft.code.iceberg.logical import (
    Block,
    PreBlock,
    Qubit,
    borrow,
    cx_between_blocks,
    cx_dynq,
    cx_transversal,
    discard,
    free_dynq,
    measure_all,
    restore,
    try_alloc_dynq,
    zz_phase_between_blocks,
    zz_phase_dynq,
)
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
    assert types_extn.types == {
        "block": iceberg_types.iceberg_block_def,
        "borrowed_block": iceberg_types.iceberg_borrowed_block_def,
        "pre_block": iceberg_types.iceberg_pre_block_def,
        "qubit": iceberg_types.iceberg_qubit_def,
    }
    assert len(ops_extn.operations) == 89
    for op_name, op_def in ops_extn.operations.items():
        op_def_name = op_name if op_name.endswith("_dynq") else f"{op_name}_def"
        assert op_def == iceberg_ops.__getattribute__(op_def_name)


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
        "try_alloc_zero",
        "check_pre_block",
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
        "y",
        "z",
        "all_but_one_x",
        "all_but_one_z",
        "x_with_all_but_one_z",
        "z_with_all_but_one_x",
        "fan_out",
        "fan_in",
        "rx",
        "ry",
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
        "cx_between_blocks",
        "xx_phase_between_blocks",
        "yy_phase_between_blocks",
        "zz_phase_between_blocks",
    ]:
        assert (
            iceberg_ops.__getattribute__(op_name)(3, 1, 2).op_def()
            == ops_extn.operations[op_name]
        )
    # Ops that take a variable number of inputs and outputs:
    for op_name in ["borrow", "borrow_more", "restore_some", "restore"]:
        assert (
            iceberg_ops.__getattribute__(op_name)(1, 3).op_def()
            == ops_extn.operations[op_name]
        )


def test_guppy_bindings_smoke() -> None:
    """Smoke test: use Guppy to construct a logical HUGR using ops that cover
    all the different signatures from the extension, and check that we can run
    compilation passes on the result."""

    @guppy
    def main() -> None:
        b0 = Block[8]()
        b1 = PreBlock[8]().check().unwrap()
        q0 = Qubit()
        q0.y()
        q0.rz(-0.5)
        bb0, q_arr0 = borrow(b0, array(3))
        cx_dynq(q0, q_arr0[0])
        q_arr1 = bb0.borrow_more(array(1, 2))
        zz_phase_dynq(q_arr0[0], q_arr1[1], 0.5)
        bb0.restore_some(q_arr1)
        b0 = restore(bb0, q_arr0)
        b0.all_h()
        b0.x(2)
        b0.zz(3, 4)
        b1.rx(5, 0.5)
        b1.all_ry(0.25)
        b1.zz_phase(6, 7, 0.5)
        cx_between_blocks(b0, b1, 7, 3)
        zz_phase_between_blocks(b0, b1, 1, 0, 0.25)
        cx_transversal(b0, b1)
        maybe_q1 = try_alloc_dynq()
        if maybe_q1.is_some():
            q1 = maybe_q1.unwrap()
            cx_dynq(q0, q1)
            free_dynq(q1)
        else:
            maybe_q1.unwrap_nothing()
        [s_z, s_x] = b0.measure_syndrome()
        maybe_m1_2 = b1.try_measure_one_x(2)
        if maybe_m1_2.is_some():
            result("m1_2", maybe_m1_2.unwrap().read())
        else:
            maybe_m1_2.unwrap_nothing()
        result("s_z", s_z.read())
        result("s_x", s_x.read())
        m0 = measure_all(b0).decode()
        result("m0_2", m0[2])
        discard(b1)
        maybe_mq0 = q0.try_measure_x()
        if maybe_mq0.is_some():
            result("mq0", maybe_mq0.unwrap().read())
        else:
            maybe_mq0.unwrap_nothing()
        free_dynq(q0)

    pkg = main.compile()
    h = pkg.modules[0]
    Normalize()(h, inplace=True)
    InlineFunctions()(h, inplace=True)


def test_guppy_hugr() -> None:
    """Consistency check of a simple logical HUGR written in Guppy."""

    @guppy
    def main() -> None:
        b = Block[8]()
        b.all_h()
        m = measure_all(b).decode()
        result("m0", m[0])

    pkg = main.compile()
    h = pkg.modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    entrypoint = h.entrypoint
    children = h.children(entrypoint)
    # When https://github.com/Quantinuum/tket2/issues/1691 is implemented, this
    # test will have to change: all the logical ops including `alloc_zero`
    # should appear under the entrypoint node. (Possibly we may need to append a
    # final `InlineFunctions()` pass to make that happen.)
    assert {h[child].op.name() for child in children} == {
        "Input",
        "LoadFunc",  # loads the alloc_zero function
        "CallIndirect",
        "guppyft.iceberg.ops.all_h<8>",
        "guppyft.iceberg.ops.measure_all<8>",
        "guppyft.std.ops.decode<8>",
        "Const(ConstUsize(0))",
        "LoadConst",
        "collections.borrow_arr.get<8, Type(Bool)>",
        "Conditional",
        'tket.result.result_bool<"m0">',
        "tket.guppy.drop<Type(borrow_array<8, Type(Bool)>)>",
        "Output",
    }
    [all_h_node] = [child for child in children if "all_h" in h[child].op.name()]
    assert len(list(h.incoming_links(all_h_node))) == 1  # CallIndirect
    assert len(list(h.outgoing_links(all_h_node))) == 1  # free


def test_guppy_types() -> None:
    """Check the hugr block types generated by guppy."""

    @guppy
    def main() -> None:
        b = Block[8]()
        bb, q_arr = borrow(b, array(0, 1, 2))
        b = restore(bb, q_arr)
        m = measure_all(b).decode()
        result("m0", m[0])

    pkg = main.compile()
    h = pkg.modules[0]

    borrow_nodes = [
        node
        for node, node_data in h.nodes()
        if isinstance(node_data.op, ExtOp) and node_data.op.op_def().name == "borrow"
    ]
    restore_nodes = [
        node
        for node, node_data in h.nodes()
        if isinstance(node_data.op, ExtOp) and node_data.op.op_def().name == "restore"
    ]
    assert len(borrow_nodes) == 1
    assert len(restore_nodes) == 1
    borrow_nodedata = h.get(borrow_nodes[0])
    restore_nodedata = h.get(restore_nodes[0])
    assert borrow_nodedata is not None
    assert restore_nodedata is not None
    borrow_op = borrow_nodedata.op
    restore_op = restore_nodedata.op
    assert isinstance(borrow_op, ExtOp)
    assert isinstance(restore_op, ExtOp)
    borrow_sig = borrow_op.signature
    restore_sig = restore_op.signature
    assert borrow_sig is not None
    assert restore_sig is not None
    borrow_input0 = borrow_sig.input[0]
    borrow_output0 = borrow_sig.output[0]
    restore_input0 = restore_sig.input[0]
    restore_output0 = restore_sig.output[0]
    assert isinstance(borrow_input0, ExtType)
    assert isinstance(borrow_output0, ExtType)
    assert isinstance(restore_input0, ExtType)
    assert isinstance(restore_output0, ExtType)
    assert borrow_input0.type_def.name == "block"
    assert borrow_output0.type_def.name == "borrowed_block"
    assert restore_input0.type_def.name == "borrowed_block"
    assert restore_output0.type_def.name == "block"
