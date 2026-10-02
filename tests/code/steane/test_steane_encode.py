import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from guppylang import guppy
from guppylang.std.angles import pi
from guppylang.std.builtins import array
from guppylang.std.debug import state_result
from guppylang.std.platform import output
from guppylang.std.qsystem.random import RNG
from guppylang.std.quantum import (
    collect_measurements,
    cx,
    cz,
    discard,
    h,
    measure,
    measure_array,
    qubit,
    rz,
    s,
    sdg,
    t,
    tdg,
    x,
    y,
    z,
)
from hugr import Hugr
from hugr.cli import validate
from hugr.package import Package
from selene_sim.backends.bundled_simulators import Coinflip

from guppyft.code.steane.encode import (
    MagicStatePrep,
    QECPolicy,
    QECStyle,
    RUSStateFactoryConf,
    SteaneBuilder,
    SteaneInstance,
)
from guppyft.decompose import ComparatorRzDecomposer, ToffoliDecomposer
from guppyft.encode import UncompilableError


def test_encoder(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        x(q0)
        h(q1)
        z(q1)
        h(q1)
        cx(q0, q1)
        r0 = measure(q0).read()
        r1 = measure(q1).read()
        output("q0", r0)
        output("q1", r1)

    pkg = main.compile()
    res = make_steane_instance(2).emulator(pkg, n_qubits=16).run().collated_shots()

    assert res == [{"q0": [1], "q1": [0]}]


def test_encoder_smoke(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        x(q0)
        y(q0)
        z(q0)
        h(q0)
        s(q0)
        sdg(q0)
        cx(q0, q1)
        cz(q0, q1)
        output("q0", measure(q0).read())
        discard(q1)

    make_steane_instance(2).emulator(main.compile(), n_qubits=16).run()


def test_encode_function_call(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    # `foo` is a public function, so the `ReplaceEncoder` pass (which defaults to
    # `GlobalScope.PRESERVE_PUBLIC`) should in principle leave its interface/behaviour
    # untouched. However, `PRESERVE_PUBLIC` is not actually enforced by the underlying
    # `ReplaceTypes` pass (a lowering pass, which ignores `preserve_interface` since its
    # purpose is to change signatures) - it still rewrites ops/types in `foo` like
    # everything else. This test just checks that the call to `foo` is still valid
    # after encoding, not that `foo`'s public interface was preserved.
    @guppy
    def main() -> None:
        q = qubit()
        foo(q)
        discard(q)

    @guppy
    def foo(q: qubit) -> None:
        pass

    pkg = main.compile()
    phys_pkg = make_steane_instance(1).encode(pkg, as_bytes=True)
    validate(phys_pkg)


def test_encoder_missing_op(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        rz(q, pi / 2)
        discard(q)

    pkg = main.compile()
    with pytest.raises(
        UncompilableError,
        match=(
            r"Error encoding `tket.quantum.Rz` at node Node\(7\). "
            r"Operation not yet supported during encoding."
        ),
    ):
        make_steane_instance(1).encode(pkg, as_bytes=True)


def test_builder_methods() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        output("q", measure(q).read())

    pkg = main.compile()

    my_policy = QECPolicy(threshold=1)
    my_policy.costs.x = 1.0

    zero_factory_conf = RUSStateFactoryConf(1, 2)

    res = (
        SteaneBuilder()
        .with_qec_policy(my_policy)
        .with_zero_factory_conf(zero_factory_conf)
        .build(n_blocks=1)
        .emulator(pkg, n_qubits=20)
        .run()
        .collated_shots()
    )

    assert res == [{"q": [1]}]


def test_encoder_control_flow(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        if measure(q0).read():  # noqa: SIM108
            q1 = qubit()
        else:
            q1 = qubit()

        output("q1", measure(q1).read())

    pkg = main.compile()
    res = make_steane_instance(2).emulator(pkg, n_qubits=20).run().collated_shots()

    assert res == [{"q1": [0]}]


def test_annotate_steane_encoding() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    SteaneBuilder().build(n_blocks=4).annotate(pkg)

    assert hugr[hugr.module_root].metadata["qnt.nexus.compilation"] == {
        "schema_version": 1,
        "ft_encoding": {
            "name": "steane",
            "params": {
                "schema_version": 1,
                "n_blocks": 4,
                "zero_factory": {
                    "size": 1,
                    "max_attempts": 5,
                },
                "magic_factory": {
                    "size": 1,
                    "max_attempts": 5,
                },
                "magic_state_prep": "flaggedft",
                "qec_policy": {
                    "style": "steane",
                    "threshold": 1,
                    "costs": {
                        "prep_zero": 0.0,
                        "prep_t": 0.0,
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0,
                        "h": 0.0,
                        "s": 0.0,
                        "sdg": 0.0,
                        "inject_t": 0.0,
                        "inject_tdg": 0.0,
                        "cx": 0.0,
                        "cz": 0.0,
                    },
                },
            },
        },
    }


def test_annotated_policy_immutable() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    policy = QECPolicy(threshold=2)
    policy.costs.x = 4.0
    instance = SteaneBuilder().with_qec_policy(policy).build(n_blocks=4)

    policy.threshold = 99
    policy.costs.x = 20.0
    instance.annotate(pkg)

    compilation = hugr[hugr.module_root].metadata["qnt.nexus.compilation"]
    policy_val = compilation["ft_encoding"]["params"]["qec_policy"]  # type: ignore[index,call-overload]
    assert policy_val["threshold"] == 2  # type: ignore[index,call-overload]
    assert policy_val["costs"]["x"] == 4.0  # type: ignore[index,call-overload]


def test_collect_measurement_encode(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    # We are using `ReplaceTypes` to replace a logical steane measurement with a borrow
    # array of measurements. As borrow arrays are always linear, this means we are
    # replacing a copyable type with a linear type. This tests that the Linearizer can
    # handle the replacement.
    @guppy
    def main() -> None:
        qbs = array(qubit() for _ in range(2))
        output("qbs", collect_measurements(measure_array(qbs)))

    make_steane_instance(2).encode(main.compile(), as_bytes=True)


def test_t_encoder_smoke(make_steane_instance: Callable[[int], SteaneInstance]) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        t(q)
        discard(q)
        q = qubit()
        tdg(q)
        discard(q)

    res = (
        make_steane_instance(2)
        .emulator(main.compile(), n_qubits=17)
        .run()
        .collated_shots()
    )

    assert res == [{}]


@pytest.mark.parametrize("style", [QECStyle.Knill, QECStyle.Steane])
def test_distilled_t(style: QECStyle) -> None:
    # Coinflip ignores the state, so this only checks that distillation runs.
    @guppy
    def main() -> None:
        q = qubit()
        h(q)
        t(q)
        output("q", measure(q).read())

    policy = QECPolicy(style=style, threshold=2)
    policy.costs.cx = 1.0
    policy.costs.inject_tdg = 1.0

    res = (
        SteaneBuilder()
        .with_qec_policy(policy)
        .with_magic_state_prep(MagicStatePrep.Distillation15To1)
        .build(n_blocks=2)
        .emulator(main.compile(), n_qubits=150)
        .with_simulator(Coinflip(bias=0.0))
        .run()
        .collated_shots()
    )

    assert res == [{"q": [0]}]


def test_distillation_clifford_program() -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        x(q0)
        cx(q0, q1)
        output("q0", measure(q0).read())
        output("q1", measure(q1).read())

    res = (
        SteaneBuilder()
        .with_magic_state_prep(MagicStatePrep.Distillation15To1)
        .build(n_blocks=2)
        .emulator(main.compile(), n_qubits=16)
        .stabilizer_sim()
        .run()
        .collated_shots()
    )

    assert res == [{"q0": [1], "q1": [1]}]


def test_encode_classical(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    @guppy
    def main() -> None:
        pass

    res = (
        make_steane_instance(1)
        .emulator(main.compile(), n_qubits=1)
        .run()
        .collated_shots()
    )
    assert res == [{}]


def test_realtime_rz_encoder(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:

    @guppy
    def main() -> None:
        rng = RNG(1234)

        target = qubit()
        h(target)
        rz(target, rng.random_angle())
        discard(target)
        output("success", 1)

        rng.discard()

    pkg = main.compile()

    rz_decomposer = ComparatorRzDecomposer(epsilon=0.01, max_attempts=15)
    rz_decomposer.then(ToffoliDecomposer()).run(pkg.modules[0], inplace=True)

    # Original block + one block for magic + ancilla space for Rz
    n_blocks = 1 + 1 + rz_decomposer.n_ancillas()

    res = (
        make_steane_instance(n_blocks)
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
def test_steane_encode_suite(
    request: pytest.FixtureRequest,
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    root_dir = request.config.rootpath
    hugr_dir = root_dir / "tests" / "resources" / "hugrs" / "guppylang-test-exports"
    for fname in Path.iterdir(hugr_dir):
        fpath = hugr_dir / fname
        with Path.open(fpath, "rb") as f:
            hugr0 = Hugr.from_bytes(f.read())
            pkg0 = hugr0.to_package()
            pkg1 = make_steane_instance(8).encode(pkg0, as_bytes=True)
            validate(pkg1)


def test_steane_state_result(
    make_steane_instance: Callable[[int], SteaneInstance],
) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        state_result("q", q)
        discard(q)

    pkg = main.with_minimal_opt().compile()

    with pytest.raises(
        UncompilableError,
        match=re.escape("Unsupported extensions found: frozenset({'tket.debug'})"),
    ):
        make_steane_instance(1).compile(pkg)
