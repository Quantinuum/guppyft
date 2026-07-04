from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.builtins import Function
from guppylang.std.quantum import cx, h, qubit
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode


@guppy
@no_type_check
def bit_flip_logical_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def bit_flip_physical_identity_double_block(
    first_block: array[qubit, 3], second_block: array[qubit, 3]
) -> None:
    pass


@guppy
@no_type_check
def bit_flip_non_ft_zero() -> array[qubit, 3]:
    return array(qubit() for _ in range(3))


@guppy
@no_type_check
def bit_flip_choi_state_double_block(
    unitary: Function[[array[qubit, 3], array[qubit, 3]], None],
) -> tuple[array[qubit, 3], array[qubit, 3], array[qubit, 3], array[qubit, 3]]:

    first_control_block = bit_flip_non_ft_zero()
    first_target_block = bit_flip_non_ft_zero()

    second_control_block = bit_flip_non_ft_zero()
    second_target_block = bit_flip_non_ft_zero()

    # First logical Bell pair
    # Apply logical H
    h(first_control_block[0])
    cx(first_control_block[0], first_control_block[1])
    cx(first_control_block[0], first_control_block[2])
    # Apply transversal CX
    cx(first_control_block[0], first_target_block[0])
    cx(first_control_block[1], first_target_block[1])
    cx(first_control_block[2], first_target_block[2])

    # Second logical Bell pair
    h(second_control_block[0])
    cx(second_control_block[0], second_target_block[0])

    cx(second_control_block[0], second_control_block[1])
    cx(second_control_block[0], second_control_block[2])

    cx(second_target_block[0], second_target_block[1])
    cx(second_target_block[0], second_target_block[2])

    unitary(first_target_block, second_target_block)

    return (
        first_control_block,
        first_target_block,
        second_control_block,
        second_target_block,
    )


BIT_FLIP_GENERATORS = pauli.StringSet.from_cmpnts(
    pauli.Strings.from_str("Z0 Z1, Z1 Z2", 3)
)

BIT_FLIP_DEF = StabilizerCode(
    num_physical_qubits=3,
    num_logical_qubits=1,
    distance=1,
    generators=BIT_FLIP_GENERATORS,
    x_logicals=pauli.String.from_str("X0 X1 X2").into(pauli.Strings),
    z_logicals=pauli.String.from_str("Z0 I1 I2").into(pauli.Strings),
)
