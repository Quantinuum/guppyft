from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.platform import output

import guppyft.code.toy_k2.logical as k2
from guppyft.code.toy_k2.encode import ToyK2Builder


def test_block_logicals() -> None:

    @guppy
    def main() -> None:

        # Create two Bell pairs across the two blocks
        blk0 = k2.Block()
        blk1 = k2.Block()
        k2.h_all(blk0)
        k2.cx_transversal(blk0, blk1)
        k2.qed_cycle(blk0)
        m0 = k2.measure_z_all(blk0).decode()
        m1 = k2.measure_z_all(blk1).decode()
        output("left_pair", m0[0] == m1[0])
        output("right_pair", m0[1] == m1[1])

        # Create a GHZ state between two blocks
        blk0 = k2.prep_zero_plus_ft()
        blk1 = k2.Block()
        k2.cx_inter(blk0, 0, blk1, 0)
        k2.cx_inter(blk0, 0, blk1, 1)
        k2.cx_intra(blk0, 1)
        m0 = k2.measure_z_all(blk0).decode()
        m1 = k2.measure_z_all(blk1).decode()
        output("ghz", m0[0] == m0[1] and m1[0] == m1[1] and m0[0] == m1[1])

        # Create a TT|++> state and apply some ops on both logical qubits
        blk = k2.prep_t_states_non_ft()
        k2.t_all(blk)  # SS|++>
        k2.s_all(blk)  # ZZ|++>
        k2.h_all(blk)  # XX|++>
        m = k2.measure_z_all(blk).decode()
        output("parallel", m[0] and m[1])  # Both true

        # Create an SS|++> state and use addressable gates on it
        blk = k2.prep_y_states_non_ft()  # SS|++>
        k2.s(blk, 0)  # ZS|++>
        k2.sdg(blk, 1)  # ZI|++>
        k2.t(blk, 1)  # ZT|++>
        k2.tdg(blk, 1)  # ZI|++>
        k2.z(blk, 1)  # ZZ|++>
        # Measure first qubit in X basis
        k2.h(blk, 0)
        m = k2.project_z(blk, 0).decode()  # Must always be true
        output("left", m)
        # Measure the second qubit in the X basis
        k2.h(blk, 1)
        m = k2.project_z(blk, 1).decode()  # Must always be true
        output("right", m)
        # Measure the first qubit again, applying an X first on it
        k2.x(blk, 0)  # |10>
        k2.swap_intra(blk)  # |01>
        m = k2.project_z(blk, 1).decode()  # Must always be true
        output("again", m)
        k2.free(blk)

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .with_shots(10)
        .run()
        .collated_shots()
    )
    for shot in res:
        assert set(shot.keys()) == {
            "left_pair",
            "right_pair",
            "ghz",
            "parallel",
            "left",
            "right",
            "again",
        }
        assert all(v for v in shot.values())


def test_sq_dynq_logicals() -> None:

    @guppy
    def main() -> None:
        q = k2.Qubit()
        k2.x_dynq(q)
        m = k2.measure_z_dynq(q).decode()
        output("x", m)

        q = k2.Qubit()
        k2.h_dynq(q)
        k2.z_dynq(q)
        k2.h_dynq(q)
        m = k2.measure_z_dynq(q).decode()
        output("z", m)

        q = k2.Qubit()
        k2.h_dynq(q)
        k2.t_dynq(q)
        k2.s_dynq(q)
        k2.t_dynq(q)
        k2.h_dynq(q)
        m = k2.measure_z_dynq(q).decode()
        output("s", m)

        q = k2.Qubit()
        k2.h_dynq(q)
        k2.tdg_dynq(q)
        k2.sdg_dynq(q)
        k2.tdg_dynq(q)
        k2.h_dynq(q)
        m = k2.measure_z_dynq(q).decode()
        output("sdg", m)

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .with_shots(10)
        .run()
        .collated_shots()
    )
    for shot in res:
        assert shot.keys() == {"x", "z", "s", "sdg"}
        assert all(v for v in shot.values())


def test_mix_static_dynq_ops() -> None:

    @guppy
    def main() -> None:
        blk = k2.Block()
        dyn_q = k2.Qubit()
        k2.x_dynq(dyn_q)

        borrowed_q, borrowed_blk = k2.borrow(blk, 0)
        other_borrowed_q = k2.borrow_more(borrowed_blk, 1)
        k2.cx_dynq(dyn_q, borrowed_q)
        k2.cx_dynq(borrowed_q, other_borrowed_q)
        k2.restore_some(borrowed_blk, other_borrowed_q)
        blk = k2.restore(borrowed_blk, borrowed_q)
        k2.free_dynq(dyn_q)
        m = k2.measure_z_all(blk).decode()
        output("out", array(m[0], m[1]))

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .run()
        .collated_shots()
    )
    assert res == [{"out": [[1, 1]]}]


def test_k2_dynq_ops() -> None:

    @guppy
    def main() -> None:
        q0 = k2.Qubit()
        q1 = k2.Qubit()
        q2 = k2.Qubit()

        k2.x_dynq(q0)

        # As k=2, one CX is inter-block and one is intra-block
        k2.cx_dynq(q0, q1)
        k2.cx_dynq(q0, q2)

        output("q0", k2.measure_z_dynq(q0).decode())
        output("q1", k2.measure_z_dynq(q1).decode())
        output("q2", k2.measure_z_dynq(q2).decode())
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
