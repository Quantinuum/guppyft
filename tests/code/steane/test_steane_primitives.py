from typing import Any, no_type_check

import pytest
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array
from guppylang.std.lang import comptime
from guppylang.std.platform import output
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg, x, y, z

from guppyft.code.steane import primitives as steane_primitives
from guppyft.code.steane.primitives import (
    CODE_DEF,
    _measure_syndromes,
    knill_qec_cycle,
    prep_zero_non_ft,
    steane_x_qec_cycle,
    steane_z_qec_cycle,
)
from guppyft.std import LogicalBlock
from guppyft.std.distillation import Distillation15To1, Distillation15To1QECPolicy
from guppyft.std.state_factory import NoResources
from guppyft.verify import valid_clifford_implementation


@guppy
@no_type_check
def specify_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def _apply_error(block: LogicalBlock[7], loc: int, is_x_error: bool) -> None:
    if is_x_error:
        x(block.data_qs[loc])
    else:
        z(block.data_qs[loc])


def test_knill_qec_without_errors() -> None:

    @guppy
    @no_type_check
    def impl_func(block: LogicalBlock[7]) -> None:
        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(block, a0, a1)

    assert valid_clifford_implementation(
        specify_identity, impl_func, CODE_DEF, n_impl_ancillas=14
    )


@pytest.mark.parametrize("error_loc", [0, 1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("is_x_error", [True, False])
def test_knill_qec_with_errors(error_loc: int, is_x_error: bool) -> None:

    @guppy
    @no_type_check
    def impl_func(block: LogicalBlock[7]) -> None:
        _apply_error(block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        a1 = prep_zero_non_ft()
        knill_qec_cycle(block, a0, a1)

    assert valid_clifford_implementation(
        specify_identity, impl_func, CODE_DEF, n_impl_ancillas=14
    )


def test_steane_qec_without_errors() -> None:

    @guppy
    @no_type_check
    def impl_func(block: LogicalBlock[7]) -> None:
        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(block, a0)

    assert valid_clifford_implementation(
        specify_identity, impl_func, CODE_DEF, n_impl_ancillas=7
    )


@pytest.mark.parametrize("error_loc", [0, 1, 2, 3, 4, 5, 6])
@pytest.mark.parametrize("is_x_error", [True, False])
def test_steane_qec_with_errors(error_loc: int, is_x_error: bool) -> None:

    @guppy
    @no_type_check
    def impl_func(block: LogicalBlock[7]) -> None:
        _apply_error(block, comptime(error_loc), comptime(is_x_error))
        a0 = prep_zero_non_ft()
        steane_x_qec_cycle(block, a0)
        a0 = prep_zero_non_ft()
        steane_z_qec_cycle(block, a0)

    assert valid_clifford_implementation(
        specify_identity, impl_func, CODE_DEF, n_impl_ancillas=7
    )


def test_steane_measure_syndromes() -> None:
    # Note: While `_measure_syndromes` is a private function, it is used
    # as part of magic state preparation which is non-Clifford and not
    # exhaustively tested. This test is included to validate the Clifford
    # components on its own.

    @guppy
    @no_type_check
    def impl_func(block: LogicalBlock[7]) -> None:
        _measure_syndromes(block)

    assert valid_clifford_implementation(
        specify_identity, impl_func, CODE_DEF, n_impl_ancillas=3
    )


@pytest.mark.parametrize(
    ("specify_def", "implement_def"),
    [
        (x, steane_primitives.x),
        (y, steane_primitives.y),
        (z, steane_primitives.z),
        (h, steane_primitives.h),
        (s, steane_primitives.s),
        (sdg, steane_primitives.sdg),
    ],
)
def test_steane_1q_primitives(
    specify_def: GuppyFunctionDefinition[[Any], None],
    implement_def: GuppyFunctionDefinition[[Any], None],
) -> None:

    @guppy
    @no_type_check
    def specify_func(q: array[qubit, 1]) -> None:
        specify_def(q[0])

    assert valid_clifford_implementation(specify_func, implement_def, CODE_DEF)


@pytest.mark.parametrize(
    ("specify_def", "implement_def"),
    [
        (cx, steane_primitives.cx),
        (cz, steane_primitives.cz),
    ],
)
def test_steane_2q_primitives(
    specify_def: GuppyFunctionDefinition[[Any], None],
    implement_def: GuppyFunctionDefinition[[Any], None],
) -> None:

    @guppy
    @no_type_check
    def specify_func(q0: array[qubit, 1], q1: array[qubit, 1]) -> None:
        specify_def(q0[0], q1[0])

    assert valid_clifford_implementation(specify_func, implement_def, CODE_DEF)


def test_t_gate() -> None:

    @guppy
    def test() -> None:
        blk = steane_primitives.prep_zero_non_ft()
        steane_primitives.h(blk)
        for _ in range(4):
            a = steane_primitives.prep_t_state_ft().force_check().unwrap()
            steane_primitives.inject_t(blk, a)
        steane_primitives.h(blk)
        res = steane_primitives.measure_z(blk)
        output("res", steane_primitives.decode(res))

    res = test.emulator(n_qubits=20).run().collated_shots()

    assert res == [{"res": [1]}]


def test_t_gate_with_non_ft_t_state() -> None:

    @guppy
    def test() -> None:
        blk = steane_primitives.prep_zero_non_ft()
        steane_primitives.h(blk)
        for _ in range(4):
            a = steane_primitives.prep_t_state_non_ft()
            steane_primitives.inject_t(blk, a)
        steane_primitives.h(blk)
        res = steane_primitives.measure_z(blk)
        output("res", steane_primitives.decode(res))

    res = test.emulator(n_qubits=14).run().collated_shots()

    assert res == [{"res": [1]}]


def test_distillation_ops() -> None:
    # A distillation round needs more than 112 qubits, so only check it compiles.

    @guppy
    @no_type_check
    def no_qec(resources: NoResources, q: LogicalBlock[7]) -> None:
        pass

    @guppy
    @no_type_check
    def prep_zero(resources: NoResources) -> LogicalBlock[7]:
        return steane_primitives.prep_zero_non_ft()

    @guppy
    @no_type_check
    def test() -> None:
        policy = Distillation15To1QECPolicy(1.0, 0.0, 0.0, 0.0, 0.0)
        ops = steane_primitives.distillation_ops()
        Distillation15To1(ops).prepare(
            NoResources(), prep_zero, no_qec, policy
        ).discard()

    test.compile()
