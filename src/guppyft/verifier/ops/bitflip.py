from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import cx, h, qubit


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
    unitary: Callable[[array[qubit, 3], array[qubit, 3]], None],
) -> tuple[array[qubit, 3], array[qubit, 3], array[qubit, 3], array[qubit, 3]]:

    first_control_block = bit_flip_non_ft_zero()
    first_target_block = bit_flip_non_ft_zero()

    second_control_block = bit_flip_non_ft_zero()
    second_target_block = bit_flip_non_ft_zero()

    # First logical Bell pair
    h(first_control_block[0])
    cx(first_control_block[0], first_target_block[0])

    cx(first_control_block[0], first_control_block[1])
    cx(first_control_block[0], first_control_block[2])

    cx(first_target_block[0], first_target_block[1])
    cx(first_target_block[0], first_target_block[2])

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
