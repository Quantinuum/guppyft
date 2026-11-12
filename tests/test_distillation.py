"""Tests for 15-to-1 magic state distillation."""

from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, comptime, output
from guppylang.std.collections import empty_queue
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
    DistillationFactory,
    DistillationOps,
    DistillationPreBlock,
    DistillationQECPolicy,
)


@guppy.struct
class _NoContext:
    pass


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
def _no_qec(context: _NoContext, q: qubit) -> None:
    pass


@guppy
@no_type_check
def _zero(context: _NoContext) -> qubit:
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
        ops = DistillationOps(_prep_t, h, sdg, z, cx, measure, _read)
        policy = DistillationQECPolicy(1.0, 0.0, 0.0, 0.0, 0.0)
        factory: DistillationFactory[qubit, Measurement, _NoContext, 1] = (
            DistillationFactory(ops, _zero, _no_qec, policy, 1, empty_queue())
        )
        q = factory.get_state(_NoContext())
        factory.discard()
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
        ops = DistillationOps(_prep_t, h, sdg, z, cx, measure, _read)
        outcomes = array(_flag(b) for b in comptime(bits))
        q = qubit()
        h(q)
        result = DistillationPreBlock(q, ops, outcomes).force_check()
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
        ops = DistillationOps(_prep_s, h, z, z, cx, measure, _read)
        qec_policy = DistillationQECPolicy(
            comptime(policy[0]),
            comptime(policy[1]),
            comptime(policy[2]),
            comptime(policy[3]),
            comptime(policy[4]),
        )
        factory: DistillationFactory[qubit, Measurement, _QECCalls, 1] = (
            DistillationFactory(
                ops, _zero_with_calls, _count_qec, qec_policy, 1, empty_queue()
            )
        )
        calls = _QECCalls(0)
        q = factory.get_state(calls)
        factory.discard()
        output("qec_calls", calls.n)
        sdg(q)
        h(q)
        output("m", measure(q).read())

    shot = main.emulator(n_qubits=17).stabilizer_sim().run().collated_shots()[0]
    assert shot["qec_calls"] == [expected_calls]
    assert shot["m"] == [False]


@guppy.struct
class _ZeroCount:
    n: int


@guppy
@no_type_check
def _counted_zero(count: _ZeroCount) -> qubit:
    count.n += 1
    return qubit()


@guppy
@no_type_check
def _no_qec_counted(count: _ZeroCount, q: qubit) -> None:
    pass


def _s_factory_program(max_attempts: int) -> GuppyFunctionDefinition[[], None]:
    """Two states from a factory of S|+> twin rounds, run two at a time."""

    @guppy
    @no_type_check
    def main() -> None:
        ops = DistillationOps(_prep_s, h, z, z, cx, measure, _read)
        policy = DistillationQECPolicy(1.0, 0.0, 0.0, 0.0, 0.0)
        factory: DistillationFactory[qubit, Measurement, _ZeroCount, 2] = (
            DistillationFactory(
                ops,
                _counted_zero,
                _no_qec_counted,
                policy,
                comptime(max_attempts),
                empty_queue(),
            )
        )
        count = _ZeroCount(0)
        for _ in range(2):
            q = factory.get_state(count)
            sdg(q)
            h(q)
            output("m", measure(q).read())
        output("zeros", count.n)
        factory.discard()

    return main  # type: ignore[no-any-return]


def test_factory_uses_surplus_round() -> None:
    main = _s_factory_program(max_attempts=5)
    shot = main.emulator(n_qubits=20).stabilizer_sim().run().collated_shots()[0]
    assert shot["m"] == [False, False]
    # One batch of two rounds serves both requests
    assert shot["zeros"] == [32]


def test_factory_exits_when_out_of_attempts() -> None:
    main = _s_factory_program(max_attempts=0)
    result = main.emulator(n_qubits=20).stabilizer_sim().run()
    tags = result.collated_shots()[0].keys()
    assert "exit: DistillationFactory ran out of attempts!" in tags
