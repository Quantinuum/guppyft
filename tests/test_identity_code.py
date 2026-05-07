from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.angles import angle
from guppylang.std.builtins import array, result
from guppylang.std.qsystem import zz_phase
from guppylang.std.quantum import (
    cx,
    discard,
    measure,
    measure_array,
    project_z,
    qubit,
    x,
)
from selene_sim.backends.bundled_simulators import Stim

from guppyft.encoder import encode

from .utils.identity_code import identity_code_gen


def test_qalloc_measure() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        measure(q)

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [{"_MeasureFree": [0], "_QAlloc": [0]}]


def test_qalloc_project_z_discard() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        result("project_z", project_z(q))
        discard(q)

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {"_Measure": [0], "_QAlloc": [0], "_QFree": [0], "project_z": [0]}
    ]


def test_x() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        result("q", measure(q))

    id_code = identity_code_gen(n_qubits=1)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {"_MeasureFree": [0], "_QAlloc": [0], "_X": [0], "q": [1]}
    ]


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
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0], "_CX": [0], "ctl": [0], "tgt": [0]},
    ]


def test_qubit_array() -> None:
    @guppy
    def main() -> None:
        qb_arr = array(qubit() for _ in range(2))
        measure_array(qb_arr)

    id_code = identity_code_gen(n_qubits=2)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=2).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0]}
    ]


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
        {"_QAlloc": [0, 0], "exit: get_next_addr: No more qubits to allocate": [1]}
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

    assert runner.run().collated_shots() == [
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0], "qb": [0, 0]}
    ]


def test_qec_policy() -> None:
    @guppy
    def main() -> None:
        qb = qubit()
        x(qb)
        measure(qb)

    costs = {"X": 1, "IDLE_X": 0, "CX": 0, "IDLE_CX": 0}

    id_code = identity_code_gen(n_qubits=1, qec_budget=1, costs=costs)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {
            "_MeasureFree": [0],
            "_QAlloc": [0],
            "_X": [0],
            "qec_counter": [[1]],
        }
    ]


def test_zz_phase() -> None:
    @guppy
    def main() -> None:
        q0, q1 = qubit(), qubit()
        zz_phase(q0, q1, angle(0.0))
        result("ctl", measure(q0))
        result("tgt", measure(q1))

    id_code = identity_code_gen(n_qubits=2)

    encoded_pkg = encode(main, id_code)
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=2).with_simulator(Stim())

    assert runner.run().collated_shots() == [
        {
            "_MeasureFree": [0, 0],
            "_QAlloc": [0, 0],
            "_ZZPhase": [0],
            "ctl": [0],
            "tgt": [0],
        },
    ]
