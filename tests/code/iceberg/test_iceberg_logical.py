from collections import Counter
from math import pi
from typing import no_type_check

import numpy as np
import pytest
from guppylang import guppy
from guppylang.std.builtins import result
from hugr.build.dfg import Dfg
from hugr.cli import validate
from hugr.ext import UsedExtensionResolver
from hugr.ops import DFG, Const, ExtOp, Input, LoadConst, Output
from hugr.std.float import FLOAT_T, FloatVal
from hugr.std.int import int_t
from hugr.tys import BoundedNatArg, ExtType, FunctionType, Option, Type
from tket.passes import InlineFunctions, Normalize
from tket_exts import measurement

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
    from_borrowed,
    measure_all,
    pauli_exp_all_x,
    pauli_exp_all_x_except_at,
    pauli_exp_all_x_except_z_at,
    pauli_exp_all_y,
    pauli_exp_all_z,
    pauli_exp_all_z_except_at,
    pauli_exp_all_z_except_x_at,
    restore,
    ry,
    ry_dynq,
    to_borrowed,
    try_alloc_dynq,
    xx_phase_dynq,
    yy_phase_dynq,
    zz_phase_between_blocks,
    zz_phase_dynq,
)
from guppyft.extensions import iceberg_ops, iceberg_types, std_types


def test_hugr() -> None:
    """Test that we can build a simple hugr out of Iceberg operations."""
    block6type = iceberg_types.iceberg_block(6)
    assert block6type.type_def.name == "block"
    assert block6type.args == [BoundedNatArg(6)]
    block6op = iceberg_ops.pauli_exp_all_x_except_at(6)
    assert block6op.name() == "guppyft.iceberg.ops.pauli_exp_all_x_except_at<6>"
    dfg = Dfg(block6type, int_t(6), FLOAT_T)
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
    [in0, in1, in2] = dfg_sig.input
    assert isinstance(in0, ExtType)
    assert isinstance(in1, ExtType)
    assert in0.type_def.name == "block"
    assert in0.args == [BoundedNatArg(6)]
    assert in1 == int_t(6)
    assert in2 == FLOAT_T


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
    assert len(ops_extn.operations) == 61
    assert str(ops_extn.version) == "0.4.0"
    for op_name, op_def in ops_extn.operations.items():
        assert op_def == iceberg_ops.__getattribute__(f"{op_name}_def")


@pytest.mark.parametrize(
    "op_name",
    [
        "all_x",
        "all_y",
        "all_z",
        "pauli_exp_all_x",
        "pauli_exp_all_y",
        "pauli_exp_all_z",
        "all_h",
        "cx_transversal",
        "alloc_zero",
        "try_alloc_zero",
        "check_pre_block",
        "free",
        "measure_syndrome",
        "measure_all",
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
        "rz",
        "pauli_exp_all_x_except_at",
        "pauli_exp_all_z_except_at",
        "pauli_exp_all_x_except_z_at",
        "pauli_exp_all_z_except_x_at",
        "try_measure_one_x",
        "try_measure_one_z",
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
        "to_borrowed",
        "borrow",
        "restore",
        "from_borrowed",
    ],
)
def test_op_instantiations(op_name: str) -> None:
    assert (
        iceberg_ops.__getattribute__(op_name)(6).op_def()
        == iceberg_ops().operations[op_name]
    )


@pytest.mark.parametrize(
    "opname",
    [
        "alloc_dynq",
        "try_alloc_dynq",
        "free_dynq",
        "x_dynq",
        "y_dynq",
        "z_dynq",
        "rx_dynq",
        "rz_dynq",
        "xx_phase_dynq",
        "yy_phase_dynq",
        "zz_phase_dynq",
        "cx_dynq",
        "try_measure_x_dynq",
        "try_measure_z_dynq",
    ],
)
def test_resolve_extensions_dynq(opname: str) -> None:
    """Regression test for not resolving all dependencies."""
    op = iceberg_ops.__getattribute__(opname)
    assert len(op.args) == 0
    resolver = UsedExtensionResolver()
    op._resolve_used_extensions(resolver)
    unused = resolver.result().unresolved_extensions
    assert iceberg_types().name not in unused
    assert std_types().name not in unused


@pytest.mark.parametrize(
    ("op_name", "n_blocks", "n_indices", "n_angles"),
    [
        ("x", 1, 1, 0),
        ("y", 1, 1, 0),
        ("z", 1, 1, 0),
        ("xx", 1, 2, 0),
        ("yy", 1, 2, 0),
        ("zz", 1, 2, 0),
        ("all_but_one_x", 1, 1, 0),
        ("all_but_one_z", 1, 1, 0),
        ("x_with_all_but_one_z", 1, 1, 0),
        ("z_with_all_but_one_x", 1, 1, 0),
        ("fan_out", 1, 1, 0),
        ("fan_in", 1, 1, 0),
        ("rx", 1, 1, 1),
        ("rz", 1, 1, 1),
        ("pauli_exp_all_x_except_at", 1, 1, 1),
        ("pauli_exp_all_z_except_at", 1, 1, 1),
        ("pauli_exp_all_x_except_z_at", 1, 1, 1),
        ("pauli_exp_all_z_except_x_at", 1, 1, 1),
        ("xx_phase", 1, 2, 1),
        ("yy_phase", 1, 2, 1),
        ("zz_phase", 1, 2, 1),
        ("cx", 1, 2, 0),
        ("swap", 1, 2, 0),
        ("xx_phase_between_blocks", 2, 2, 1),
        ("yy_phase_between_blocks", 2, 2, 1),
        ("zz_phase_between_blocks", 2, 2, 1),
        ("cx_between_blocks", 2, 2, 0),
        ("try_measure_one_x", 1, 1, 0),
        ("try_measure_one_z", 1, 1, 0),
    ],
)
def test_indexed_op_signatures(
    op_name: str, n_blocks: int, n_indices: int, n_angles: int
) -> None:
    """All indexed operations have value inputs and a single size parameter."""
    block = iceberg_types.iceberg_block(6)
    op = getattr(iceberg_ops, op_name)(6)
    inputs: list[Type] = [block for _ in range(n_blocks)]
    inputs.extend([int_t(6)] * n_indices)
    inputs.extend([FLOAT_T] * n_angles)
    outputs: list[Type] = [block for _ in range(n_blocks)]
    if op_name.startswith("try_measure_one"):
        outputs = [Option(measurement.measurement_t), block]
    assert op.args == [BoundedNatArg(6)]
    assert op.signature == FunctionType(inputs, outputs)
    poly_sig = op.op_def().signature.poly_func
    assert poly_sig is not None
    assert len(poly_sig.params) == 1
    assert len(poly_sig.body.input) == len(inputs)
    assert len(poly_sig.body.output) == len(outputs)


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
        bb0 = b0.to_borrowed()
        qb0 = borrow(bb0, 3)
        cx_dynq(q0, qb0)
        qb1 = bb0.borrow(1)
        qb2 = bb0.borrow(2)
        zz_phase_dynq(qb0, qb2, 0.5)
        bb0.restore(qb1)
        bb0.restore(qb2)
        restore(bb0, qb0)
        b0 = Block.from_borrowed(bb0)
        b0.all_h()
        b0.x(2)
        b0.zz(3, 4)
        b1.rx(5, 0.5)
        b1.pauli_exp_all_y(0.25)
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


def test_pauli_exponential_bindings_resolve_and_normalize() -> None:
    """Free functions and methods lower runtime indices/angles to the same ops."""

    @guppy
    @no_type_check
    def main(block: Block[4], i: int, phase: float) -> None:
        pauli_exp_all_x(block, phase)
        pauli_exp_all_y(block, phase)
        pauli_exp_all_z(block, phase)
        pauli_exp_all_x_except_at(block, i, phase)
        pauli_exp_all_z_except_at(block, i, phase)
        pauli_exp_all_x_except_z_at(block, i, phase)
        pauli_exp_all_z_except_x_at(block, i, phase)
        block.pauli_exp_all_x(phase)
        block.pauli_exp_all_y(phase)
        block.pauli_exp_all_z(phase)
        block.pauli_exp_all_x_except_at(i, phase)
        block.pauli_exp_all_z_except_at(i, phase)
        block.pauli_exp_all_x_except_z_at(i, phase)
        block.pauli_exp_all_z_except_x_at(i, phase)

    h = main.compile_function().modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    assert not h.used_extensions().unresolved_extensions
    expected = {
        "pauli_exp_all_x": 0,
        "pauli_exp_all_y": 0,
        "pauli_exp_all_z": 0,
        "pauli_exp_all_x_except_at": 1,
        "pauli_exp_all_z_except_at": 1,
        "pauli_exp_all_x_except_z_at": 1,
        "pauli_exp_all_z_except_x_at": 1,
    }
    found: Counter[str] = Counter()
    block_type = iceberg_types.iceberg_block(4)
    for node in h.children(h.entrypoint):
        op = h[node].op
        if isinstance(op, ExtOp) and op.op_def().name in expected:
            name = op.op_def().name
            found[name] += 1
            inputs: list[Type] = [block_type]
            inputs.extend([int_t(6)] * expected[name])
            inputs.append(FLOAT_T)
            signature = FunctionType(inputs, [block_type])
            assert op.outer_signature() == signature
            assert op.args == [BoundedNatArg(4)]
    assert found == Counter(dict.fromkeys(expected, 2))
    validate(h.to_bytes())


def test_guppy_hugr() -> None:
    """Consistency check of a simple logical HUGR written in Guppy."""

    @guppy
    def main() -> None:
        b = Block[8]()
        b.all_h()
        discard(b)

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
        "guppyft.iceberg.ops.free<8>",
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
        bb = to_borrowed(b)
        qb = borrow(bb, 0)
        restore(bb, qb)
        b = from_borrowed(bb)
        discard(b)

    pkg = main.compile()
    h = pkg.modules[0]

    block = iceberg_types.iceberg_block(8)
    borrowed_block = iceberg_types.iceberg_borrowed_block(8)
    qubit = iceberg_types.iceberg_qubit()
    expected = {
        "to_borrowed": FunctionType([block], [borrowed_block]),
        "borrow": FunctionType([borrowed_block, int_t(6)], [qubit, borrowed_block]),
        "restore": FunctionType([borrowed_block, qubit], [borrowed_block]),
        "from_borrowed": FunctionType([borrowed_block], [block]),
    }
    found: Counter[str] = Counter()
    for _node, data in h.nodes():
        op = data.op
        if isinstance(op, ExtOp) and op.op_def().name in expected:
            name = op.op_def().name
            found[name] += 1
            assert op.args == [BoundedNatArg(8)]
            assert op.outer_signature() == expected[name]
    assert found == Counter(dict.fromkeys(expected, 1))
    validate(h.to_bytes())


def test_dynamic_qubit_bindings_resolve_and_normalize() -> None:
    """Compile every dynamic-qubit binding through the public logical API."""

    @guppy
    def main() -> None:
        q0 = Qubit()
        q1 = Qubit()
        q0.x()
        q0.y()
        q0.z()
        q0.rx(0.25)
        q0.ry(0.5)
        q0.rz(0.75)
        xx_phase_dynq(q0, q1, 0.25)
        yy_phase_dynq(q0, q1, 0.5)
        zz_phase_dynq(q0, q1, 0.75)
        cx_dynq(q0, q1)
        mx = q0.try_measure_x()
        if mx.is_some():
            result("x", mx.unwrap().read())
        else:
            mx.unwrap_nothing()
        mz = q1.try_measure_z()
        if mz.is_some():
            result("z", mz.unwrap().read())
        else:
            mz.unwrap_nothing()
        allocated = try_alloc_dynq()
        if allocated.is_some():
            free_dynq(allocated.unwrap())
        else:
            allocated.unwrap_nothing()
        free_dynq(q0)
        free_dynq(q1)

    h = main.compile().modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    assert not h.used_extensions().unresolved_extensions
    dynamic_ops = {
        data.op.op_def().name
        for _, data in h.nodes()
        if isinstance(data.op, ExtOp)
        and data.op.op_def().get_extension().name == "guppyft.iceberg.ops"
    }
    assert dynamic_ops == {
        "alloc_dynq",
        "try_alloc_dynq",
        "free_dynq",
        "x_dynq",
        "y_dynq",
        "z_dynq",
        "rx_dynq",
        "rz_dynq",
        "xx_phase_dynq",
        "yy_phase_dynq",
        "zz_phase_dynq",
        "cx_dynq",
        "try_measure_x_dynq",
        "try_measure_z_dynq",
    }


@pytest.mark.parametrize(
    "binding", ["block_function", "block_method", "dynamic_function", "dynamic_method"]
)
def test_ry_compositions(binding: str) -> None:
    """The public Ry APIs implement the correct unitary using only Rx and Rz."""

    @guppy
    @no_type_check
    def block_function(block: Block[4], i: int, phase: float) -> None:
        ry(block, i, phase)

    @guppy
    @no_type_check
    def block_method(block: Block[4], i: int, phase: float) -> None:
        block.ry(i, phase)

    @guppy
    def dynamic_function(qubit: Qubit, phase: float) -> None:
        ry_dynq(qubit, phase)

    @guppy
    def dynamic_method(qubit: Qubit, phase: float) -> None:
        qubit.ry(phase)

    main = {
        "block_function": block_function,
        "block_method": block_method,
        "dynamic_function": dynamic_function,
        "dynamic_method": dynamic_method,
    }[binding]
    h = main.compile_function().modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    validate(h.to_bytes())
    assert not {"ry", "ry_dynq"} & iceberg_ops().operations.keys()

    [input_node] = [
        node for node in h.children(h.entrypoint) if isinstance(h[node].op, Input)
    ]
    dynamic = binding.startswith("dynamic")
    phase_port = 1 if dynamic else 2
    for phase in [0.0, pi / 4, -1.3, pi, 2 * pi]:
        unitary = np.eye(2, dtype=complex)
        wire = input_node.out(0)
        for _ in range(3):
            [target] = h.linked_ports(wire)
            op = h[target.node].op
            assert isinstance(op, ExtOp)
            name = op.op_def().name
            assert name in ({"rx_dynq", "rz_dynq"} if dynamic else {"rx", "rz"})
            if not dynamic:
                assert list(h.linked_ports(target.node.inp(1))) == [input_node.out(1)]
            [angle_wire] = h.linked_ports(target.node.inp(phase_port))
            if angle_wire == input_node.out(phase_port):
                theta = phase
            else:
                assert isinstance(h[angle_wire.node].op, LoadConst)
                [constant_wire] = h.linked_ports(angle_wire.node.inp(0))
                constant = h[constant_wire.node].op
                assert isinstance(constant, Const)
                assert isinstance(constant.val, FloatVal)
                theta = constant.val.v
            pauli = np.array(
                [[0, 1], [1, 0]] if name.startswith("rx") else [[1, 0], [0, -1]]
            )
            rotation = np.cos(theta / 2) * np.eye(2) - 1j * np.sin(theta / 2) * pauli
            unitary = rotation @ unitary
            wire = target.node.out(0)
        [output] = h.linked_ports(wire)
        assert isinstance(h[output.node].op, Output)
        expected = np.array(
            [
                [np.cos(phase / 2), -np.sin(phase / 2)],
                [np.sin(phase / 2), np.cos(phase / 2)],
            ]
        )
        np.testing.assert_allclose(unitary, expected, atol=1e-14)


@pytest.mark.parametrize("normalize", [False, True])
def test_borrow_restore_match_extension_signatures(normalize: bool) -> None:
    """Guppy borrow/restore calls must match extension signatures with static k."""

    @guppy
    def main() -> None:
        block = Block[8]()
        bblock = block.to_borrowed()
        qb0 = borrow(bblock, 0)
        qb1 = borrow(bblock, 1)
        qb2 = bblock.borrow(2)
        cx_dynq(qb0, qb1)
        bblock.restore(qb0)
        bblock.restore(qb1)
        bblock.restore(qb2)
        block = Block.from_borrowed(bblock)
        discard(block)

    [h] = main.compile().modules
    expected = {
        "borrow": iceberg_ops.borrow(8),
        "to_borrowed": iceberg_ops.to_borrowed(8),
        "from_borrowed": iceberg_ops.from_borrowed(8),
        "restore": iceberg_ops.restore(8),
    }
    if normalize:
        InlineFunctions()(h, inplace=True)
        Normalize()(h, inplace=True)
    found = set()
    for _node, data in h.nodes():
        op = data.op
        if (
            isinstance(op, ExtOp)
            and op.op_def().get_extension().name == "guppyft.iceberg.ops"
            and op.op_def().name in expected
        ):
            name = op.op_def().name
            found.add(name)
            assert op.args == expected[name].args
            assert op.outer_signature() == expected[name].outer_signature()
    assert found == expected.keys()
    validate(h.to_bytes())
