from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.lang import comptime
from guppylang.std.mem import mem_swap
from guppylang.std.platform import output
from guppylang.std.quantum import cx, h, qubit, s, x, z

from guppyft.code.toy_k2 import primitives as toy_k2
from guppyft.code.toy_k2.primitives import CODE_DEF
from guppyft.code.util import LogicalBlock
from guppyft.verifier import (
    compute_verification_signterms_double_block_unitary,
    compute_verification_signterms_single_block_state,
    compute_verification_signterms_single_block_unitary,
)


@pytest.mark.parametrize("idx", [0, 1])
def test_x(idx: int) -> None:

    @guppy
    @no_type_check
    def specify_func(qs: array[qubit, 2]) -> None:
        x(qs[comptime(idx)])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.x(block, comptime(idx))

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


@pytest.mark.parametrize("idx", [0, 1])
def test_z(idx: int) -> None:

    @guppy
    @no_type_check
    def specify_func(qs: array[qubit, 2]) -> None:
        z(qs[comptime(idx)])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.z(block, comptime(idx))

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


def test_h_all() -> None:

    @guppy
    @no_type_check
    def specify_func(qs: array[qubit, 2]) -> None:
        for i in range(len(qs)):
            h(qs[i])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.h_all(block)

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


@pytest.mark.parametrize("target", [0, 1])
def test_cx_intra(target: int) -> None:

    @guppy
    @no_type_check
    def specify_func(qs: array[qubit, 2]) -> None:
        cx(qs[comptime(1 - target)], qs[comptime(target)])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.cx_intra(block, comptime(target))

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


def test_cx_transversal() -> None:

    @guppy
    @no_type_check
    def specify_func(ctl: array[qubit, 2], tgt: array[qubit, 2]) -> None:
        cx(ctl[0], tgt[0])
        cx(ctl[1], tgt[1])

    @guppy
    @no_type_check
    def impl_func(ctl: array[qubit, 4], tgt: array[qubit, 4]) -> None:
        c_block = LogicalBlock(array(ctl.take(i) for i in range(4)))
        t_block = LogicalBlock(array(tgt.take(i) for i in range(4)))

        toy_k2.cx_transversal(c_block, t_block)

        for i in range(4):
            ctl.put(c_block.data_qs.take(i), i)
            tgt.put(t_block.data_qs.take(i), i)
        c_block.discard()
        t_block.discard()

    sem, impl = compute_verification_signterms_double_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


def test_swap_intra() -> None:

    @guppy
    @no_type_check
    def specify_func(qs: array[qubit, 2]) -> None:
        mem_swap(qs[0], qs[1])

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.swap_intra(block)

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


def test_prep_zero() -> None:

    @guppy
    @no_type_check
    def specify_func() -> array[qubit, 2]:
        return array(qubit() for _ in range(2))

    @guppy
    @no_type_check
    def impl_func() -> array[qubit, 4]:
        block = toy_k2.prep_zero_ft().force_check().unwrap()

        arr = array(block.data_qs.take(i) for i in range(4))
        block.discard()

        return arr

    sem, impl = compute_verification_signterms_single_block_state(
        specify_func,
        impl_func,
        CODE_DEF,
        num_ancilla_qubits=1,
    )
    assert sem == impl


def test_prep_y_states() -> None:

    @guppy
    @no_type_check
    def specify_func() -> array[qubit, 2]:
        qs = array(qubit() for _ in range(2))
        for i in range(len(qs)):
            h(qs[i])
            s(qs[i])
        return qs

    @guppy
    @no_type_check
    def impl_func() -> array[qubit, 4]:
        block = toy_k2.prep_y_states_non_ft()

        arr = array(block.data_qs.take(i) for i in range(4))
        block.discard()

        return arr

    sem, impl = compute_verification_signterms_single_block_state(
        specify_func,
        impl_func,
        CODE_DEF,
    )
    assert sem == impl


def test_prep_t_states() -> None:
    """This is not an exhaustive test."""

    @guppy
    @no_type_check
    def main() -> None:
        block = toy_k2.prep_t_states_non_ft()

        # Running a QED cycle confirms that the stabilizers
        # of the code are satisfied
        toy_k2.qed_cycle(block)

        output("success", 1)
        block.discard()

    out = main.emulator(n_qubits=6).run().collated_shots()
    assert out == [{"success": [1]}]


@pytest.mark.parametrize("x0", [0, 1])
@pytest.mark.parametrize("x1", [0, 1])
def test_measure_z_all(x0: int, x1: int) -> None:

    @guppy
    @no_type_check
    def main() -> None:
        block = toy_k2.prep_zero_ft().force_check().unwrap()

        if comptime(x0) == 1:
            toy_k2.x(block, comptime(0))
        if comptime(x1) == 1:
            toy_k2.x(block, comptime(1))

        res = toy_k2.measure_z_all(block)
        output("result", res)

    out = main.emulator(n_qubits=5).run().collated_shots()
    assert out[0]["result"] == [[x0, x1]]


@pytest.mark.parametrize("idx", [0, 1])
@pytest.mark.parametrize("x0", [0, 1])
@pytest.mark.parametrize("x1", [0, 1])
def test_measure_z(idx: int, x0: int, x1: int) -> None:

    @guppy
    @no_type_check
    def main() -> None:
        block = toy_k2.prep_zero_ft().force_check().unwrap()

        if comptime(x0) == 1:
            toy_k2.x(block, comptime(0))
        if comptime(x1) == 1:
            toy_k2.x(block, comptime(1))

        res = toy_k2.measure_z(block, comptime(idx))
        output("result", res)

        block.discard()

    exp_result = x0 if idx == 0 else x1

    out = main.emulator(n_qubits=6).run().collated_shots()
    assert out[0]["result"] == [exp_result]


def test_qed_cycle_without_errors() -> None:

    @guppy
    @no_type_check
    def specify_func(arr: array[qubit, 2]) -> None:
        pass

    @guppy
    @no_type_check
    def impl_func(arr: array[qubit, 4]) -> None:
        block = LogicalBlock(array(arr.take(i) for i in range(4)))

        toy_k2.qed_cycle(block)

        for i in range(4):
            arr.put(block.data_qs.take(i), i)
        block.discard()

    sem, impl = compute_verification_signterms_single_block_unitary(
        specify_func,
        impl_func,
        CODE_DEF,
        num_ancilla_qubits=2,
    )
    assert sem == impl


@pytest.mark.parametrize("error_loc", [0, 1, 2, 3])
@pytest.mark.parametrize("is_x_error", [True, False])
def test_qed_cycle_with_errors(error_loc: int, is_x_error: bool) -> None:

    @guppy
    @no_type_check
    def main() -> None:
        block = toy_k2.prep_zero_ft().force_check().unwrap()

        if comptime(is_x_error):
            x(block.data_qs[comptime(error_loc)])
        else:
            z(block.data_qs[comptime(error_loc)])

        toy_k2.qed_cycle(block)

        block.discard()

    if is_x_error:
        expected_msg = "exit: A QED cycle detected an X error."
    else:
        expected_msg = "exit: A QED cycle detected a Z error."

    out = main.emulator(n_qubits=6).run().collated_shots()
    assert out[0] == {expected_msg: [1]}
