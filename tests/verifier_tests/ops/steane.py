from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import cx, h, qubit, s, sdg


@guppy
@no_type_check
def steane_logical_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def steane_logical_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def steane_physical_identity(block: array[qubit, 7]) -> None:
    pass


@guppy
@no_type_check
def steane_physical_identity_double_block(
    first_block: array[qubit, 7], second_block: array[qubit, 7]
) -> None:
    pass


@guppy
@no_type_check
def steane_physical_h(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        h(block[i])


@guppy
@no_type_check
def steane_logical_h(block: array[qubit, 1]) -> None:
    h(block[0])


@guppy
@no_type_check
def steane_logical_s(block: array[qubit, 1]) -> None:
    s(block[0])


@guppy
@no_type_check
def steane_physical_s(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        sdg(block[i])


@guppy
@no_type_check
def steane_logical_sdg(block: array[qubit, 1]) -> None:
    sdg(block[0])


@guppy
@no_type_check
def steane_physical_sdg(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        s(block[i])


@guppy
@no_type_check
def steane_logical_cx(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    cx(first_block[0], second_block[0])


@guppy
@no_type_check
def steane_physical_cx(
    first_block: array[qubit, 7], second_block: array[qubit, 7]
) -> None:
    for i in range(len(first_block)):
        cx(first_block[i], second_block[i])


@guppy
@no_type_check
def steane_non_ft_zero() -> array[qubit, 7]:
    """Non fault-tolerant zero state preparation."""
    block = array(qubit() for _ in range(7))

    plus_ids = array(0, 4, 6)
    for i in plus_ids:
        h(block[i])

    cx_pairs = array((0, 1), (4, 5), (6, 3), (6, 5), (4, 2), (0, 3), (4, 1), (3, 2))
    for c, t in cx_pairs:
        cx(block[c], block[t])

    return block


@guppy
@no_type_check
def steane_choi_state(
    unitary: Callable[[array[qubit, 7]], None],
) -> tuple[array[qubit, 7], array[qubit, 7]]:
    control_block = steane_non_ft_zero()
    target_block = steane_non_ft_zero()

    steane_physical_h(control_block)
    steane_physical_cx(control_block, target_block)

    unitary(target_block)

    return control_block, target_block


@guppy
@no_type_check
def steane_choi_state_double_block(
    unitary: Callable[[array[qubit, 7], array[qubit, 7]], None],
) -> tuple[
    array[qubit, 7],
    array[qubit, 7],
    array[qubit, 7],
    array[qubit, 7],
]:
    first_control_block = steane_non_ft_zero()
    first_target_block = steane_non_ft_zero()

    second_control_block = steane_non_ft_zero()
    second_target_block = steane_non_ft_zero()

    steane_physical_h(first_control_block)
    steane_physical_cx(first_control_block, first_target_block)
    steane_physical_h(second_control_block)
    steane_physical_cx(second_control_block, second_target_block)

    # Apply unitary to the target blocks
    unitary(first_target_block, second_target_block)

    return (
        first_control_block,
        first_target_block,
        second_control_block,
        second_target_block,
    )
