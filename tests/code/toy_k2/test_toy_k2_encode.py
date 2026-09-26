import os
from pathlib import Path

import pytest
from guppylang import guppy
from guppylang.std import quantum as qlib
from guppylang.std.angles import pi
from guppylang.std.builtins import array
from guppylang.std.platform import output
from guppylang.std.qsystem.random import RNG
from hugr import Hugr
from hugr.cli import validate
from selene_sim.backends.bundled_simulators import Coinflip

from guppyft.code.toy_k2.encode import (
    QEDPolicy,
    ToyK2Builder,
)
from guppyft.decompose import ComparatorRzDecomposer, ToffoliDecomposer
from guppyft.encode import UncompilableError


def test_encoder() -> None:

    @guppy
    def main() -> None:
        q0 = qlib.qubit()
        q1 = qlib.qubit()
        qlib.x(q0)
        qlib.h(q1)
        qlib.z(q1)
        qlib.h(q1)
        qlib.cx(q0, q1)
        r0 = qlib.measure(q0).read()
        r1 = qlib.measure(q1).read()
        output("q0", r0)
        output("q1", r1)

    pkg = main.compile()
    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=16)
        .run()
        .collated_shots()
    )

    assert res == [{"q0": [1], "q1": [0]}]


def test_encoder_smoke() -> None:

    @guppy
    def main() -> None:
        q0 = qlib.qubit()
        q1 = qlib.qubit()
        qlib.x(q0)
        # qlib.y(q0)  # TODO: Consider adding
        qlib.z(q0)
        qlib.h(q0)
        qlib.s(q0)
        qlib.sdg(q0)
        qlib.cx(q0, q1)
        # qlib.cz(q0, q1)  # TODO: Consider adding
        output("q0", qlib.measure(q0).read())
        qlib.discard(q1)

    ToyK2Builder().build(n_blocks=2).emulator(main.compile(), n_qubits=16).run()


def test_encoder_for_dynamic_op() -> None:
    @guppy
    def main() -> None:
        q0 = qlib.qubit()
        q1 = qlib.qubit()
        q2 = qlib.qubit()
        qlib.x(q0)
        qlib.z(q0)
        qlib.h(q0)
        qlib.s(q0)
        qlib.sdg(q0)
        qlib.t(q0)
        qlib.tdg(q0)
        qlib.h(q0)
        qlib.cx(q0, q1)
        qlib.cx(q0, q2)
        output("q", qlib.measure(q0).read())
        output("q", qlib.measure(q1).read())
        output("q", qlib.measure(q2).read())

    compiler = ToyK2Builder().build(n_blocks=4)
    pkg = main.with_minimal_opt().compile()
    assert compiler._spec.compile is not None
    logical = compiler._spec.compile(pkg)

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
        compiler.emulator(pkg, n_qubits=10)
        .with_seed(123)
        .with_shots(10)
        .run()
        .collated_shots()
    )

    assert res == [{"q": [1, 1, 1]}] * 10


def test_encoder_missing_op() -> None:
    @guppy
    def main() -> None:
        q = qlib.qubit()
        qlib.rz(q, pi / 2)
        qlib.discard(q)

    pkg = main.compile()
    with pytest.raises(
        UncompilableError,
        match=(
            r"Error encoding `tket.quantum.Rz` at node Node\(7\). "
            r"Operation not yet supported during encoding."
        ),
    ):
        ToyK2Builder().build(n_blocks=1).encode(pkg, as_bytes=True)


def test_builder_methods() -> None:
    @guppy
    def main() -> None:
        q = qlib.qubit()
        qlib.x(q)
        output("q", qlib.measure(q).read())

    pkg = main.compile()

    my_policy = QEDPolicy(threshold=1)
    my_policy.costs.x = 1.0

    res = (
        ToyK2Builder()
        .with_qed_policy(my_policy)
        .build(n_blocks=1)
        .emulator(pkg, n_qubits=20)
        .run()
        .collated_shots()
    )

    assert res == [{"q": [1]}]


def test_encoder_control_flow() -> None:
    @guppy
    def main() -> None:
        q0 = qlib.qubit()
        if qlib.measure(q0).read():  # noqa: SIM108
            q1 = qlib.qubit()
        else:
            q1 = qlib.qubit()

        output("q1", qlib.measure(q1).read())

    pkg = main.compile()
    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=20)
        .run()
        .collated_shots()
    )

    assert res == [{"q1": [0]}]


def test_collect_measurement_encode() -> None:
    @guppy
    def main() -> None:
        qbs = array(qlib.qubit() for _ in range(2))
        output("qbs", qlib.collect_measurements(qlib.measure_array(qbs)))

    ToyK2Builder().build(n_blocks=2).encode(main.compile(), as_bytes=True)


def test_t_encoder_smoke() -> None:
    @guppy
    def main() -> None:
        q = qlib.qubit()
        qlib.t(q)
        qlib.discard(q)
        q = qlib.qubit()
        qlib.tdg(q)
        qlib.discard(q)

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(main.compile(), n_qubits=17)
        .run()
        .collated_shots()
    )

    assert res == [{}]


def test_encode_classical() -> None:
    @guppy
    def main() -> None:
        pass

    res = (
        ToyK2Builder()
        .build(n_blocks=1)
        .emulator(main.compile(), n_qubits=1)
        .run()
        .collated_shots()
    )
    assert res == [{}]


@pytest.mark.xfail(reason="CZ not currently supported")  # TODO
def test_realtime_rz_encoder() -> None:

    @guppy
    def main() -> None:
        rng = RNG(1234)

        target = qlib.qubit()
        qlib.h(target)
        qlib.rz(target, rng.random_angle())
        qlib.discard(target)
        output("success", 1)

        rng.discard()

    pkg = main.compile()

    rz_decomposer = ComparatorRzDecomposer(epsilon=0.01, max_attempts=15)
    rz_decomposer.then(ToffoliDecomposer()).run(pkg.modules[0], inplace=True)

    # Original block + one block for magic + ancilla space for Rz
    n_blocks = 1 + 1 + rz_decomposer.n_ancillas()

    res = (
        ToyK2Builder()
        .build(n_blocks=n_blocks)
        .emulator(pkg, n_qubits=7 * n_blocks + 6)
        .with_simulator(Coinflip(bias=0.0))
        .run()
        .collated_shots()
    )

    assert res == [{"success": [1]}]


@pytest.mark.skipif(
    os.getenv("GUPPYFT_RUN_LONG_TESTS") != "true",
    reason="GUPPYFT_RUN_LONG_TESTS is not set to 'true'",
)
def test_encode_suite(request: pytest.FixtureRequest) -> None:
    root_dir = request.config.rootpath
    hugr_dir = root_dir / "tests" / "resources" / "hugrs" / "guppylang-test-exports"
    for fname in Path.iterdir(hugr_dir):
        fpath = hugr_dir / fname
        with Path.open(fpath, "rb") as f:
            hugr0 = Hugr.from_bytes(f.read())
            pkg0 = hugr0.to_package()
            toy_k2 = ToyK2Builder().build(n_blocks=8)
            pkg1 = toy_k2.encode(pkg0, as_bytes=True)
            validate(pkg1)
