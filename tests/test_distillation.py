"""Tests for 15-to-1 magic state distillation."""

from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.builtins import array, comptime, output
from guppylang.std.quantum import (
    Measurement,
    cx,
    h,
    measure,
    qubit,
    s,
    sdg,
    t,
    tdg,
    x,
    z,
)

from guppyft.std.distillation import (
    Distillation15To1,
    Distillation15To1Ops,
    Distillation15To1QECPolicy,
    DistillationFlags,
    _distillation_check,
)
from guppyft.std.state_factory import NoResources


@guppy
@no_type_check
def _read(m: Measurement) -> bool:
    return m.read()


@guppy
@no_type_check
def _prep_t() -> qubit:
    q = qubit()
    h(q)
    t(q)
    return q


@guppy
@no_type_check
def _prep_s() -> qubit:
    q = qubit()
    h(q)
    s(q)
    return q


@guppy
@no_type_check
def _no_qec(resources: NoResources, q: qubit) -> None:
    pass


@guppy
@no_type_check
def _zero(resources: NoResources) -> qubit:
    return qubit()


@guppy
@no_type_check
def _flag(value: bool) -> Measurement:
    q = qubit()
    if value:
        x(q)
    return measure(q)


def test_distills_t_state() -> None:
    @guppy
    @no_type_check
    def main() -> None:
        ops = Distillation15To1Ops(_prep_t, h, sdg, z, cx, measure, _read)
        policy = Distillation15To1QECPolicy(1.0, 0.0, 0.0, 0.0, 0.0)
        result = (
            Distillation15To1(ops)
            .prepare(NoResources(), _zero, _no_qec, policy)
            .force_check()
        )
        q = result.unwrap()
        # Undo the ideal T|+> preparation
        tdg(q)
        h(q)
        output("m", measure(q).read())

    shots = main.emulator(n_qubits=17).statevector_sim().with_shots(3).run()
    assert all(shot["m"] == [False] for shot in shots.collated_shots())


@pytest.mark.parametrize(
    ("ones", "accepted", "corrected"),
    [
        ([], True, False),
        ([5], False, False),
        ([8], False, False),
        ([1, 2], False, False),
        ([1, 2, 3], True, True),
    ],
)
def test_check(ones: list[int], accepted: bool, corrected: bool) -> None:
    """Checks the X stabilizers and Z correction on given outcomes of blocks 1 to 15."""
    bits = [j in ones for j in range(1, 16)]

    @guppy
    @no_type_check
    def main() -> None:
        ops = Distillation15To1Ops(_prep_t, h, sdg, z, cx, measure, _read)
        outcomes = array(_flag(b) for b in comptime(bits))
        q = qubit()
        h(q)
        result = _distillation_check(q, DistillationFlags(ops, outcomes))
        if result.is_some():
            out = result.unwrap()
            h(out)
            output("accepted", True)
            output("corrected", measure(out).read())
        else:
            result.unwrap_nothing()
            output("accepted", False)
            output("corrected", False)

    shot = main.emulator(n_qubits=16).stabilizer_sim().run().collated_shots()[0]
    assert shot["accepted"] == [accepted]
    assert shot["corrected"] == [corrected]


@guppy.struct
class _QECCalls:
    n: int


@guppy
@no_type_check
def _count_qec(calls: _QECCalls, q: qubit) -> None:
    calls.n += 1


@guppy
@no_type_check
def _zero_with_calls(calls: _QECCalls) -> qubit:
    return qubit()


@pytest.mark.parametrize(
    ("policy", "expected_calls"),
    [
        ((1.0, 0.0, 0.0, 0.0, 0.0), 0),
        # 16 zero states, 5 H, 25 CX on two blocks, 15 injections each followed by H
        ((1.0, 1.0, 1.0, 1.0, 1.0), 16 + 5 + 2 * 25 + 2 * 15),
        ((1.0, 0.0, 0.0, 1.0, 0.0), 2 * 25),
        # Each block takes part in 2 to 4 CX, giving a cycle per 2 CX on a block
        ((2.0, 0.0, 0.0, 1.0, 0.0), 22),
    ],
)
def test_qec_policy(
    policy: tuple[float, float, float, float, float], expected_calls: int
) -> None:
    """Uses S|+> inputs with Z corrections, which distil S|+> through the same circuit
    and can be simulated by a stabilizer simulator."""

    @guppy
    @no_type_check
    def main() -> None:
        ops = Distillation15To1Ops(_prep_s, h, z, z, cx, measure, _read)
        qec_policy = Distillation15To1QECPolicy(
            comptime(policy[0]),
            comptime(policy[1]),
            comptime(policy[2]),
            comptime(policy[3]),
            comptime(policy[4]),
        )
        calls = _QECCalls(0)
        result = (
            Distillation15To1(ops)
            .prepare(calls, _zero_with_calls, _count_qec, qec_policy)
            .force_check()
        )
        output("qec_calls", calls.n)
        q = result.unwrap()
        sdg(q)
        h(q)
        output("m", measure(q).read())

    shot = main.emulator(n_qubits=17).stabilizer_sim().run().collated_shots()[0]
    assert shot["qec_calls"] == [expected_calls]
    assert shot["m"] == [False]
