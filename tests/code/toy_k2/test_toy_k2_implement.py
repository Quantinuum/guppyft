from guppylang import guppy
from guppylang.std.platform import output
from guppylang.std.quantum import cx, h, measure, qubit, s, sdg, t, tdg, x, z

import guppyft.code.toy_k2.logical as k2
from guppyft.code.toy_k2.encode import ToyK2Builder


def test_mix_static_dynq_ops() -> None:

    @guppy
    def main() -> None:
        blk = k2.Block()
        dyn_q = k2.Qubit()

        borrowed_blk, borrowed_q = k2.borrow(blk, 0)
        k2.cx_dynq(dyn_q, borrowed_q)
        blk = k2.restore(borrowed_blk, borrowed_q)
        dyn_q.free()
        k2.measure_z_all(blk)
        output("test", 99)

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .run()
        .collated_shots()
    )
    assert res == [{"test": [99]}]


def test_k2_dynq_ops() -> None:

    @guppy
    def main() -> None:
        q0 = k2.Qubit()
        q1 = k2.Qubit()
        q2 = k2.Qubit()

        k2.x_dynq(q0)

        # As k=2, one ccx is inter-block and one is intra-block
        k2.cx_dynq(q0, q1)
        k2.cx_dynq(q0, q2)

        output("q0", q0.project_z().decode())
        output("q1", k2.project_z_dynq(q1).decode())
        output("q2", k2.project_z_dynq(q2).decode())
        q0.free()
        q1.free()
        q2.free()
        output("end", -1)

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .run()
        .collated_shots()
    )
    assert res == [{"q0": [1], "q1": [1], "q2": [1], "end": [-1]}]


def test_single_qubit_callbacks_link() -> None:
    @guppy
    def main() -> None:
        q = k2.Qubit()
        k2.x_dynq(q)
        k2.z_dynq(q)
        k2.h_dynq(q)
        k2.s_dynq(q)
        k2.sdg_dynq(q)
        k2.t_dynq(q)
        k2.tdg_dynq(q)
        q.free()

    compiler = ToyK2Builder().build(n_blocks=2)
    compiler.implement_ops(main.with_minimal_opt().compile())


def test_encoder_for_dynamic_op() -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        q2 = qubit()
        x(q0)
        z(q0)
        h(q0)
        s(q0)
        sdg(q0)
        t(q0)
        tdg(q0)
        cx(q0, q1)
        cx(q0, q2)
        output("q", measure(q0).read())
        output("q", measure(q1).read())
        output("q", measure(q2).read())

    compiler = ToyK2Builder().build(n_blocks=4)
    assert compiler._spec.compile is not None
    logical = compiler._spec.compile(main.compile())

    assert any(
        data.op.name() == "guppyft.toy_k2.ops.call_dyn_sq"
        for module in logical.modules
        for _node, data in module.nodes()
    )
    assert any(
        data.op.name() == "guppyft.toy_k2.ops.call_dyn_tq"
        for module in logical.modules
        for _node, data in module.nodes()
    )
    compiler.implement_ops(logical)

    res = (
        compiler.emulator(main.compile(), n_qubits=10)
        .with_seed(123)
        .run()
        .collated_shots()
    )

    assert res == [{"q": [1, 1, 1]}]
