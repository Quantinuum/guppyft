import cmath
import math
from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorBuilder, EmulatorError
from guppylang.std import quantum as qlib
from guppylang.std.angles import angle, pi
from guppylang.std.builtins import comptime
from guppylang.std.platform import output
from guppylang.std.quantum import cx, h, measure, qubit, rz, sdg, z
from selene_sim.backends.bundled_simulators import Quest

from guppyft.code.steane import logical, primitives
from guppyft.code.steane.encode import AdaptiveRzConf, SteaneBuilder
from guppyft.code.steane.primitives import (
    _stabilizer_indices,
    adaptive_rz,
    rotate_and_correct_rz,
)


@pytest.mark.parametrize("physical", [-0.7, -0.13, 0.001, 0.2, 0.7])
def test_syndrome_angles(physical: float) -> None:
    # Expand the physical rotations and group terms by corrected syndrome.
    checks = _stabilizer_indices()
    amplitudes = [[0j, 0j] for _ in range(8)]
    for mask in range(128):
        syndrome = sum(
            (sum((mask >> i) & 1 for i in check) % 2) << j
            for j, check in enumerate(checks)
        )
        weight = mask.bit_count()
        logical = (weight + (syndrome != 0)) % 2
        amplitudes[syndrome][logical] += (
            math.cos(physical / 2) ** (7 - weight)
            * (-1j * math.sin(physical / 2)) ** weight
        )
    t = math.tan(physical / 2)
    trivial = -2 * math.atan((7 * t**3 + t**7) / (1 + 7 * t**4))
    # Compare with Eqs. (18)-(23) of arXiv:2608.20676.
    eta = cmath.exp(1j * physical) * (7 + cmath.exp(-4j * physical)) ** 2 / 64
    assert trivial == pytest.approx(-cmath.phase(eta))
    probability = 0.0
    for syndrome, (a, b) in enumerate(amplitudes):
        expected = trivial if syndrome == 0 else 3 * physical
        assert (a - b) / (a + b) == pytest.approx(cmath.exp(1j * expected))
        probability += abs(a) ** 2 + abs(b) ** 2
    assert probability == pytest.approx(1.0)


@pytest.mark.parametrize("phase", [0.0, 0.13, -0.31, math.pi / 4, math.pi / 2, 7.1])
def test_adaptive_rz_encode(phase: float) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        h(q)
        rz(q, angle(comptime(phase / math.pi)))
        rz(q, angle(comptime(0.5 - phase / math.pi)))
        sdg(q)
        h(q)
        output("result", measure(q).read())

    results = (
        SteaneBuilder()
        .with_adaptive_rz()
        .build(n_blocks=1)
        .emulator(main.compile(), n_qubits=8)
        .with_seed(7)
        .with_shots(20)
        .run()
        .collated_shots()
    )
    assert results == [{"result": [0]}] * 20


def test_adaptive_zz_inverse_encode() -> None:
    @guppy
    @no_type_check
    def zz_inverse() -> None:
        q0, q1 = qlib.qubit(), qlib.qubit()
        qlib.h(q0)
        qlib.h(q1)

        # exp(-i 0.6 Z0 Z1 / 2)
        qlib.cx(q0, q1)
        qlib.rz(q1, angle(0.6 / float(pi)))
        qlib.cx(q0, q1)

        # exp(+i 0.6 Z0 Z1 / 2)
        qlib.cx(q0, q1)
        qlib.rz(q1, angle(-0.6 / float(pi)))
        qlib.cx(q0, q1)

        qlib.h(q0)
        qlib.h(q1)
        output("q0", qlib.measure(q0).read())
        output("q1", qlib.measure(q1).read())

    pkg = zz_inverse.with_minimal_opt().compile()
    assert (
        sum(data.op.name() == "tket.quantum.Rz" for _, data in pkg.modules[0].nodes())
        == 2
    )
    results = (
        SteaneBuilder()
        .with_adaptive_rz()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=16)
        .with_simulator(Quest())
        .with_seed(7)
        .with_shots(20)
        .run()
        .collated_shots()
    )
    assert results == [{"q0": [0], "q1": [0]}] * 20


@pytest.mark.parametrize("abort_on_dephasing", [True, False])
def test_round_limit(abort_on_dephasing: bool) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        h(q)
        rz(q, angle(0.125))
        output("result", measure(q).read())

    emulator = (
        SteaneBuilder()
        .with_adaptive_rz(
            AdaptiveRzConf(max_rounds=1, abort_on_dephasing=abort_on_dephasing)
        )
        .build(n_blocks=1)
        .emulator(main.compile(), n_qubits=8)
        .with_seed(7)
        .with_shots(40)
    )
    with pytest.raises(EmulatorError, match="Adaptive Rz exceeded max_rounds"):
        emulator.run()


@pytest.mark.parametrize("error_qubit", range(7))
def test_in_place_z_correction(error_qubit: int) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        blk = primitives.prep_zero_non_ft()
        primitives.h(blk)
        z(blk.data_qs[comptime(error_qubit)])
        output("syndrome", rotate_and_correct_rz(blk, 0.0))
        output("after_correction", rotate_and_correct_rz(blk, 0.0))
        primitives.h(blk)
        output("logical", primitives.decode(primitives.measure_z(blk)))

    result = main.emulator(n_qubits=8).with_seed(7).run().collated_shots()
    assert result == [{"syndrome": [1], "after_correction": [0], "logical": [0]}]


@pytest.mark.parametrize(
    "phase", [0.0, 1e-5, 0.13, -0.31, math.pi / 4, math.pi / 2, 7.1]
)
def test_adaptive_rz_weight_three_inverse(phase: float) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        blk = primitives.prep_zero_non_ft()
        primitives.h(blk)
        adaptive_rz(blk, comptime(phase), 1e-10, 100, 0.0, 0.5)

        # Z_L * ZZZZIII = IIIIZZZ: undo the phase on qubits 4, 5, 6.
        cx(blk.data_qs[4], blk.data_qs[6])
        cx(blk.data_qs[5], blk.data_qs[6])
        rz(blk.data_qs[6], angle(comptime(-phase / math.pi)))
        cx(blk.data_qs[5], blk.data_qs[6])
        cx(blk.data_qs[4], blk.data_qs[6])

        # We should be back in the code space and in logical |+>.
        output("syndromes", primitives._measure_x_syndromes(blk))
        primitives.h(blk)
        output("logical", primitives.decode(primitives.measure_z(blk)))

    results = (
        main.emulator(n_qubits=8).with_seed(7).with_shots(20).run().collated_shots()
    )
    assert results == [{"syndromes": [[0, 0, 0]], "logical": [0]}] * 20


def test_explicit_adaptive_rz() -> None:
    @guppy
    def main() -> None:
        q = logical.Qubit()
        q.h()
        q.adaptive_rz(0.13)
        q.adaptive_rz(-0.13)
        q.h()
        output("logical", q.measure_z().decode())

    # Explicit adaptive_rz should work with the default builder too.
    pkg = SteaneBuilder().build(n_blocks=1).implement_ops(main.compile())
    results = (
        EmulatorBuilder()
        .build(pkg, n_qubits=8)
        .with_seed(7)
        .with_shots(20)
        .run()
        .collated_shots()
    )
    assert results == [{"logical": [0]}] * 20


def _kraus_channels(physical: float, dephasing: float) -> list[tuple[complex, float]]:
    # Expand all coherent Z terms, then mix all independent stochastic Z errors.
    checks = [sum(1 << i for i in check) for check in primitives._stabilizer_indices()]
    probabilities = [0.0] * 8
    coherences = [0j] * 8
    for error in range(128):
        error_weight = error.bit_count()
        probability = dephasing**error_weight * (1 - dephasing) ** (7 - error_weight)
        amplitudes = [[0j, 0j] for _ in range(8)]
        for rotation in range(128):
            mask = error ^ rotation
            syndrome = sum(
                ((mask & check).bit_count() % 2) << j for j, check in enumerate(checks)
            )
            logical = (mask.bit_count() + (syndrome != 0)) % 2
            weight = rotation.bit_count()
            amplitudes[syndrome][logical] += (
                math.cos(physical / 2) ** (7 - weight)
                * (-1j * math.sin(physical / 2)) ** weight
            )
        for syndrome, (a, b) in enumerate(amplitudes):
            probabilities[syndrome] += probability * (abs(a) ** 2 + abs(b) ** 2)
            coherences[syndrome] += probability * (a + b) * (a - b).conjugate()
    return list(zip(coherences, probabilities, strict=True))


def test_noisy_channels() -> None:
    cases = [(a, p) for a in [0.0, -0.13, math.pi / 4] for p in [0.0, 0.02, 0.49]]

    @guppy
    @no_type_check
    def main() -> None:
        for physical, dephasing in comptime(cases):
            for nontrivial in comptime([False, True]):
                phi, noise, probability = primitives._rz_channel(
                    physical, dephasing, nontrivial
                )
                output("angle", phi)
                output("dephasing", noise)
                output("probability", probability)

    result = main.emulator(n_qubits=1).run().collated_shots()[0]
    for i, (physical, dephasing) in enumerate(cases):
        channels = _kraus_channels(physical, dephasing)
        assert sum(p for _, p in channels) == pytest.approx(1.0)
        for syndrome, (eta, probability) in enumerate(channels):
            j = 2 * i + (syndrome != 0)
            assert result["probability"][j] == pytest.approx(probability, abs=1e-14)
            if probability > 1e-14:
                actual = (1 - 2 * result["dephasing"][j]) * cmath.exp(
                    -1j * result["angle"][j]
                )
                assert actual == pytest.approx(eta / probability, abs=1e-12)


def test_noisy_angle_inversion() -> None:
    cases = [(a, p) for a in [-math.pi / 4, -0.13, 1e-5] for p in [0.0, 0.02, 0.49]]

    @guppy
    @no_type_check
    def main() -> None:
        for target, dephasing in comptime(cases):
            output("physical", primitives._physical_angle(target, dephasing))

    result = main.emulator(n_qubits=1).run().collated_shots()[0]
    for physical, (target, dephasing) in zip(result["physical"], cases, strict=True):
        eta, _ = _kraus_channels(physical, dephasing)[0]
        assert -cmath.phase(eta) == pytest.approx(target, abs=1e-12)


def test_noisy_round_tomography() -> None:
    physical = 0.3
    dephasing = 0.03

    @guppy
    @no_type_check
    def main(measure_y: bool) -> None:
        block = primitives.prep_zero_non_ft()
        primitives.h(block)
        # A measured coin applies Z with probability p, using one spare qubit.
        for i in range(7):
            coin = qlib.qubit()
            qlib.ry(
                coin, angle(comptime(2 * math.asin(math.sqrt(dephasing)) / math.pi))
            )
            if qlib.measure(coin).read():
                qlib.z(block.data_qs[i])
        output("syndrome", primitives.rotate_and_correct_rz(block, comptime(physical)))
        if measure_y:
            primitives.sdg(block)
        primitives.h(block)
        output("logical", primitives.decode(primitives.measure_z(block)))

    channels = _kraus_channels(physical, dephasing)
    emulator = main.emulator(n_qubits=8).with_seed(7).with_shots(4000)
    for measure_y in [False, True]:
        results = emulator.run(measure_y=measure_y).collated_shots()
        for syndrome in [0, 1]:
            selected = [
                r["logical"][0] for r in results if r["syndrome"][0] == syndrome
            ]
            eta, probability = channels[syndrome]
            expected_probability = probability * (7 if syndrome else 1)
            assert len(selected) / len(results) == pytest.approx(
                expected_probability, abs=0.04
            )
            expectation = (-eta.imag if measure_y else eta.real) / probability
            expected_minus = (1 - expectation) / 2
            stderr = math.sqrt(expected_minus * (1 - expected_minus) / len(selected))
            assert sum(selected) / len(selected) == pytest.approx(
                expected_minus, abs=5 * stderr + 1 / len(selected)
            )


def test_encoded_dephasing_budget() -> None:
    @guppy
    @no_type_check
    def main() -> None:
        q = qlib.qubit()
        qlib.rz(q, angle(0.1))
        qlib.discard(q)

    emulator = (
        SteaneBuilder()
        .with_adaptive_rz(AdaptiveRzConf(dephasing=0.02, max_dephasing=0.0))
        .build(n_blocks=1)
        .emulator(main.compile(), n_qubits=8)
    )
    with pytest.raises(EmulatorError, match="Adaptive Rz exceeded max_dephasing"):
        emulator.run()


@pytest.mark.parametrize("max_dephasing", [0.0, 0.5])
def test_encoded_dephasing_budget_report(max_dephasing: float) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        q = qlib.qubit()
        qlib.h(q)
        qlib.rz(q, angle(0.1))
        output("after_first_rotation", True)
        qlib.rz(q, angle(0.07))
        qlib.discard(q)
        output("completed", True)

    results = (
        SteaneBuilder()
        .with_adaptive_rz(
            AdaptiveRzConf(
                dephasing=0.02,
                max_dephasing=max_dephasing,
                abort_on_dephasing=False,
            )
        )
        .build(n_blocks=1)
        .emulator(main.with_minimal_opt().compile(), n_qubits=8)
        .with_seed(7)
        .with_shots(5)
        .run()
        .collated_shots()
    )
    expected = {"after_first_rotation": [1], "completed": [1]}
    if max_dephasing == 0.0:
        expected["adaptive_rz_dephasing_limit_hit"] = [1, 1]
    assert results == [expected] * 5
