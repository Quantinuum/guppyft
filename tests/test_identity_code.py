from guppylang import guppy
from guppylang.std.builtins import array, result
from guppylang.std.quantum import discard, measure, measure_array, qubit, x
from hugr.qsystem.result import QsysShot
from selene_sim import Stim, build

from guppyft.encoder import auto_encode

from .utils.identity_code import identity_code_gen


def test_x():
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        result("q", measure(q))

    id_code = identity_code_gen(n_qubits=1)

    prog_bytes = auto_encode(main, id_code).to_bytes()

    runner = build(prog_bytes)

    assert QsysShot(runner.run(simulator=Stim(), n_qubits=1)).entries == [("q", 1)]


def test_qubit_array():
    @guppy
    def main() -> None:
        qb_arr = array(qubit() for _ in range(2))
        result("qb_arr", measure_array(qb_arr))

    id_code = identity_code_gen(n_qubits=2)

    prog_bytes = auto_encode(main, id_code).to_bytes()

    runner = build(prog_bytes)

    assert QsysShot(runner.run(simulator=Stim(), n_qubits=2)).entries == [
        ("qb_arr", [0, 0])
    ]


def test_out_of_logical_qubits():
    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        discard(q0)
        discard(q1)

    id_code = identity_code_gen(n_qubits=1)

    prog_bytes = auto_encode(main, id_code).to_bytes()

    runner = build(prog_bytes)

    assert QsysShot(runner.run(simulator=Stim(), n_qubits=1)).entries == [
        ("exit: get_next_addr: No more qubits to allocate", 1)
    ]


def test_qubit_reuse():
    @guppy
    def main() -> None:
        qb = qubit()
        result("qb", measure(qb))
        qb = qubit()
        result("qb", measure(qb))

    id_code = identity_code_gen(n_qubits=1)

    prog_bytes = auto_encode(main, id_code).to_bytes()

    runner = build(prog_bytes)

    assert QsysShot(runner.run(simulator=Stim(), n_qubits=2)).entries == [
        ("qb", 0),
        ("qb", 0),
    ]
