from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.builtins import array, result
from guppylang.std.quantum import cx, discard, measure, measure_array, qubit, x
from selene_sim.backends.bundled_simulators import Stim

from guppyft.encoder import encode

from .utils.identity_code import identity_code_gen


def test_x() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        result("q", measure(q))

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [{"q": [1]}]


def test_cx() -> None:
    @guppy
    def main() -> None:
        ctl, tgt = qubit(), qubit()
        cx(ctl, tgt)
        result("ctl", measure(ctl))
        result("tgt", measure(tgt))

    id_code = identity_code_gen(n_qubits=2)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=2).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {"ctl": [0], "tgt": [0]},
    ]


def test_qubit_array() -> None:
    @guppy
    def main() -> None:
        qb_arr = array(qubit() for _ in range(2))
        result("qb_arr", measure_array(qb_arr))

    id_code = identity_code_gen(n_qubits=2)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=2).with_simulator(Stim())

    assert runner.run().collated_shots() == [{"qb_arr": [[0, 0]]}]


def test_out_of_logical_qubits() -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        discard(q0)
        discard(q1)

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {"exit: get_next_addr: No more qubits to allocate": [1]}
    ]


def test_qubit_reuse() -> None:
    @guppy
    def main() -> None:
        qb = qubit()
        result("qb", measure(qb))
        qb = qubit()
        result("qb", measure(qb))

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [{"qb": [0, 0]}]
