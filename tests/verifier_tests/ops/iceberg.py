from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.angles import pi
from guppylang.std.array import array
from guppylang.std.builtins import mem_swap
from guppylang.std.qsystem import zz_max, zz_phase
from guppylang.std.quantum import cx, cz, h, qubit, rx, s, sdg


@guppy
@no_type_check
def iceberg_logical_identity(block: array[qubit, 2]) -> None:
    pass


@guppy
@no_type_check
def iceberg_physical_identity(block: array[qubit, 4]) -> None:
    pass


@guppy
@no_type_check
def iceberg_intra_block_cx_logical(block: array[qubit, 2]) -> None:
    cx(block[0], block[1])


@guppy
@no_type_check
def iceberg_intra_block_cx_physical(block: array[qubit, 4]) -> None:
    mem_swap(block[3], block[1])


@guppy
@no_type_check
def iceberg_intra_block_cz_logical(block: array[qubit, 2]) -> None:
    cz(block[0], block[1])


@guppy
@no_type_check
def iceberg_intra_block_cz_physical(block: array[qubit, 4]) -> None:
    s(block[0])
    sdg(block[1])
    sdg(block[2])
    s(block[3])


@guppy
@no_type_check
def iceberg_addressable_h_logical(block: array[qubit, 2]) -> None:
    h(block[1])


@guppy
@no_type_check
def iceberg_addressable_h_physical(block: array[qubit, 4]) -> None:
    iceberg_addressable_s_physical(block)
    iceberg_addressable_rx_half_pi_physical(block)
    iceberg_addressable_s_physical(block)


@guppy
@no_type_check
def iceberg_addressable_s_logical(block: array[qubit, 2]) -> None:
    s(block[1])


@guppy
@no_type_check
def iceberg_addressable_s_physical(block: array[qubit, 4]) -> None:
    zz_max(block[2], block[3])


@guppy
@no_type_check
def iceberg_addressable_rx_half_pi_logical(block: array[qubit, 2]) -> None:
    rx(block[1], pi / 2)


@guppy
@no_type_check
def iceberg_addressable_rx_half_pi_physical(block: array[qubit, 4]) -> None:
    h(block[0])
    h(block[2])
    zz_max(block[0], block[2])
    h(block[0])
    h(block[2])


@guppy
@no_type_check
def iceberg_addressable_rx_minus_half_pi_logical(block: array[qubit, 2]) -> None:
    rx(block[1], -pi / 2)


@guppy
@no_type_check
def iceberg_addressable_rx_minus_half_pi_physical(block: array[qubit, 4]) -> None:
    h(block[0])
    h(block[2])
    zz_phase(block[0], block[2], -pi / 2)
    h(block[0])
    h(block[2])


@guppy
@no_type_check
def iceberg_double_h_logical(block: array[qubit, 2]) -> None:
    h(block[0])
    h(block[1])


@guppy
@no_type_check
def iceberg_double_h_physical(block: array[qubit, 4]) -> None:
    h(block[0])
    h(block[1])
    h(block[2])
    h(block[3])
    mem_swap(block[1], block[2])


@guppy
@no_type_check
def iceberg_interblock_zzmax_logical(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    zz_max(first_block[0], second_block[0])
    zz_max(first_block[1], second_block[1])


@guppy
@no_type_check
def iceberg_interblock_zzmax_physical(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    cx(first_block[0], second_block[0])
    cx(first_block[1], second_block[1])
    zz_max(second_block[0], second_block[1])
    cx(first_block[0], second_block[0])
    cx(first_block[1], second_block[1])

    cx(first_block[2], second_block[2])
    cx(first_block[3], second_block[3])
    zz_max(second_block[2], second_block[3])
    cx(first_block[2], second_block[2])
    cx(first_block[3], second_block[3])


@guppy
@no_type_check
def iceberg_transversal_cx_logical(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    cx(first_block[0], second_block[0])
    cx(first_block[1], second_block[1])


@guppy
@no_type_check
def iceberg_transversal_cx_physical(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    cx(first_block[0], second_block[0])
    cx(first_block[1], second_block[1])
    cx(first_block[2], second_block[2])
    cx(first_block[3], second_block[3])


@guppy
@no_type_check
def iceberg_logical_identity_double_block(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    pass


@guppy
@no_type_check
def iceberg_physical_identity_double_block(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    pass


@guppy
@no_type_check
def iceberg_non_ft_zero() -> array[qubit, 4]:
    block = array(qubit() for _ in range(4))
    h(block[2])
    cx(block[2], block[1])
    cx(block[2], block[3])
    cx(block[1], block[0])
    return block


@guppy
@no_type_check
def iceberg_choi_state(
    unitary: Callable[[array[qubit, 4]], None],
) -> tuple[array[qubit, 4], array[qubit, 4]]:
    control_block = iceberg_non_ft_zero()
    target_block = iceberg_non_ft_zero()

    iceberg_double_h_physical(control_block)
    iceberg_transversal_cx_physical(control_block, target_block)

    unitary(target_block)

    return control_block, target_block


@guppy
@no_type_check
def iceberg_choi_state_double_block(
    unitary: Callable[[array[qubit, 4], array[qubit, 4]], None],
) -> tuple[array[qubit, 4], array[qubit, 4], array[qubit, 4], array[qubit, 4]]:
    first_control_block = iceberg_non_ft_zero()
    first_target_block = iceberg_non_ft_zero()
    second_control_block = iceberg_non_ft_zero()
    second_target_block = iceberg_non_ft_zero()

    iceberg_double_h_physical(first_control_block)
    iceberg_double_h_physical(second_control_block)

    iceberg_transversal_cx_physical(first_control_block, first_target_block)
    iceberg_transversal_cx_physical(second_control_block, second_target_block)

    unitary(first_target_block, second_target_block)

    return (
        first_control_block,
        first_target_block,
        second_control_block,
        second_target_block,
    )
