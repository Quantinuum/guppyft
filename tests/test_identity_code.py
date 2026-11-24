from typing import no_type_check

from guppylang import guppy
from guppylang.emulator import EmulatorBuilder, EmulatorResult
from guppylang.std.angles import angle
from guppylang.std.builtins import array, result
from guppylang.std.qsystem.helios import zz_phase
from guppylang.std.quantum import (
    cx,
    discard,
    measure,
    measure_array,
    project_z,
    qubit,
    x,
)
from hugr.package import Package
from selene_sim.backends.bundled_simulators import Stim

from tests.utils.identity_code import (
    IdentityBuilder,
    IdentityInstance,
    IdentityQECPolicy,
)


def _identity(*, n_qubits: int) -> IdentityInstance:
    return IdentityBuilder.new(n_qubits=n_qubits).build()


def _run_with_stim(pkg: Package | bytes, *, n_qubits: int) -> EmulatorResult:
    return EmulatorBuilder().build(pkg, n_qubits=n_qubits).with_simulator(Stim()).run()


def test_qalloc_measure() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        measure(q)

    pkg = _identity(n_qubits=1).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=1).collated_shots() == [
        {"_MeasureFree": [0], "_QAlloc": [0]}
    ]


def test_qalloc_project_z_discard() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        result("project_z", project_z(q).read())
        discard(q)

    pkg = _identity(n_qubits=1).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=1).collated_shots() == [
        # From guppylang v1.0.0a6, `project_z` has been updated to return `Measurement`.
        # As the op `tket.quantum.Measure` still returns a bool, the way this is
        # achieved is by calling `measure` on the qubit and then initializing a new
        # qubit in the correct state. This is why `_QAlloc` is called twice and
        # the results include `_MeasureFree`.
        {"_MeasureFree": [0], "_QAlloc": [0, 0], "_QFree": [0], "project_z": [0]}
    ]


def test_x() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        result("q", measure(q).read())

    pkg = _identity(n_qubits=1).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=1).collated_shots() == [
        {"_MeasureFree": [0], "_QAlloc": [0], "_X": [0], "q": [1]}
    ]


def test_cx() -> None:
    @guppy
    def main() -> None:
        ctl, tgt = qubit(), qubit()
        cx(ctl, tgt)
        result("ctl", measure(ctl).read())
        result("tgt", measure(tgt).read())

    pkg = _identity(n_qubits=2).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0], "_CX": [0], "ctl": [0], "tgt": [0]},
    ]


def test_zz_phase() -> None:
    @guppy
    @no_type_check
    def main() -> None:
        ctl, tgt = qubit(), qubit()
        zz_phase(ctl, tgt, angle(0.0))
        result("ctl", measure(ctl).read())
        result("tgt", measure(tgt).read())

    pkg = _identity(n_qubits=2).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {
            "_MeasureFree": [0, 0],
            "_QAlloc": [0, 0],
            "_ZZPhase": [0],
            "ctl": [0],
            "tgt": [0],
        },
    ]


def test_qubit_array() -> None:
    @guppy
    def main() -> None:
        qb_arr = array(qubit() for _ in range(2))
        measure_array(qb_arr)

    pkg = _identity(n_qubits=2).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0]}
    ]


def test_out_of_logical_qubits() -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        discard(q0)
        discard(q1)

    pkg = _identity(n_qubits=1).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {"_QAlloc": [0, 0], "exit: get_next_addr: No more qubits to allocate": [1]}
    ]


def test_qubit_reuse() -> None:
    @guppy
    def main() -> None:
        qb = qubit()
        result("qb", measure(qb).read())
        qb = qubit()
        result("qb", measure(qb).read())

    pkg = _identity(n_qubits=1).encode(main.compile(), as_bytes=True)

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {"_MeasureFree": [0, 0], "_QAlloc": [0, 0], "qb": [0, 0]}
    ]


def test_qec_policy() -> None:
    @guppy
    def main() -> None:
        qb = qubit()
        x(qb)
        measure(qb)

    costs = IdentityQECPolicy.OperationCosts()
    costs.x = (1, 0)
    costs.cx = (0, 0)

    pkg = (
        IdentityBuilder.new(n_qubits=1)
        .with_qec_policy(IdentityQECPolicy(threshold=1, costs=costs))
        .build()
        .encode(main.compile(), as_bytes=True)
    )

    assert _run_with_stim(pkg, n_qubits=2).collated_shots() == [
        {
            "_MeasureFree": [0],
            "_QAlloc": [0],
            "_X": [0],
            "qec_counter": [[1]],
        }
    ]
