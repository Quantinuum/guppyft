from guppylang import guppy
from guppylang.std.builtins import result
from hugr.build.dfg import Dfg
from hugr.ops import DFG
from hugr.tys import ExtType
from tket.passes import InlineFunctions, Normalize

from guppyft.extensions import steane_ops, steane_types
from guppyft.logical.steane import Qubit, cx, prep_magic_for_t_like


def test_hugr() -> None:
    """Test that we can build a simple hugr out of Steane operations."""
    qubit_type = steane_types.steane_qubit()
    assert qubit_type.type_def.name == "qubit"
    assert qubit_type.args == []
    qubit_op = steane_ops.cx()
    assert qubit_op.name() == "guppyft.steane.ops.cx"
    dfg = Dfg(qubit_type, qubit_type)
    node = dfg.add_op(qubit_op, *dfg.inputs())
    dfg.set_outputs(node)
    h = dfg.hugr
    h_extn_ids = h.used_extensions().ids()
    assert "guppyft.steane.ops" in h_extn_ids
    assert "guppyft.steane.types" in h_extn_ids
    [fndef] = h.children(h.module_root)
    _inp, _out, dfg = h.children(fndef)
    dfg_data = h.get(dfg)
    assert dfg_data is not None
    dfg_op = dfg_data.op
    assert isinstance(dfg_op, DFG)
    dfg_sig = dfg_op.signature
    [in0, in1] = dfg_sig.input
    assert isinstance(in0, ExtType)
    assert in0.type_def.name == "qubit"
    assert in0.args == []
    assert isinstance(in1, ExtType)
    assert in1.type_def.name == "qubit"
    assert in1.args == []


def test_exported_extensions() -> None:
    ops_extn = steane_ops()
    types_extn = steane_types()
    assert len(ops_extn.types) == 0
    assert len(types_extn.operations) == 0
    assert types_extn.types == {
        "qubit": steane_types.steane_qubit_def,
        "measurement": steane_types.steane_measurement_def,
    }
    assert len(ops_extn.operations) == 14
    for op_name, op_def in ops_extn.operations.items():
        assert op_def == steane_ops.__getattribute__(f"{op_name}_def")


def test_op_instantiations() -> None:
    ops_extn = steane_ops()
    # No operations take indices
    assert len(ops_extn.operations) == 14
    for op_name in ops_extn.operations:
        assert (
            steane_ops.__getattribute__(op_name)().op_def()
            == ops_extn.operations[op_name]
        )


def test_guppy_bindings_smoke() -> None:
    """Smoke test: use Guppy to construct a logical HUGR using ops that cover
    all the different signatures from the extension, and check that we can run
    compilation passes on the result."""

    @guppy
    def main() -> None:
        q0 = Qubit()
        q0.x()
        q1 = Qubit()
        cx(q0, q1)
        q1.free()
        magic = prep_magic_for_t_like()
        q0.inject_magic_for_t(magic)
        result("q0", q0.measure_z().decode())

    pkg = main.compile()
    h = pkg.modules[0]
    Normalize()(h, inplace=True)
    InlineFunctions()(h, inplace=True)


def test_guppy_hugr() -> None:
    """Consistency check of a simple logical HUGR written in Guppy."""

    @guppy
    def main() -> None:
        q = Qubit()
        q.h()
        result("a", q.measure_z().decode())

    pkg = main.compile()
    h = pkg.modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    entrypoint = h.entrypoint
    children = h.children(entrypoint)
    # When https://github.com/Quantinuum/tket2/issues/1691 is implemented, this
    # test will have to change: all the logical ops including `prep_zero`
    # should appear under the entrypoint node. (Possibly we may need to append a
    # final `InlineFunctions()` pass to make that happen.)
    assert {h[child].op.name() for child in children} == {
        "Input",
        "guppyft.steane.ops.prep_zero",
        "guppyft.steane.ops.h",
        "guppyft.steane.ops.measure_z",
        "Output",
        "guppyft.steane.ops.decode",
        'tket.result.result_bool<"a">',
    }
    [h_node] = [child for child in children if "h" in h[child].op.name()]
    assert len(list(h.incoming_links(h_node))) == 1  # CallIndirect
    assert len(list(h.outgoing_links(h_node))) == 1  # free
