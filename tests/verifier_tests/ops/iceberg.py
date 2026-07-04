from typing import no_type_check

from guppylang import guppy
from guppylang.std.angles import pi
from guppylang.std.array import array
from guppylang.std.builtins import Function
from guppylang.std.mem import mem_swap
from guppylang.std.qsystem.helios import zz_max, zz_phase
from guppylang.std.quantum import cx, cz, h, qubit, rx, rz, s, sdg
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode


@guppy
@no_type_check
def logical_identity(block: array[qubit, 2]) -> None:
    pass


@guppy
@no_type_check
def physical_identity(block: array[qubit, 4]) -> None:
    pass


@guppy
@no_type_check
def intra_block_cx_logical(block: array[qubit, 2]) -> None:
    cx(block[0], block[1])


@guppy
@no_type_check
def intra_block_cx_physical(block: array[qubit, 4]) -> None:
    mem_swap(block[3], block[1])


@guppy
@no_type_check
def intra_block_cz_logical(block: array[qubit, 2]) -> None:
    cz(block[0], block[1])


@guppy
@no_type_check
def intra_block_cz_physical(block: array[qubit, 4]) -> None:
    s(block[0])
    sdg(block[1])
    sdg(block[2])
    s(block[3])


@guppy
@no_type_check
def addressable_h_logical(block: array[qubit, 2]) -> None:
    h(block[1])


# Technically this is -H due to the global phase difference between S/Rz and V/Rx.
@guppy
@no_type_check
def addressable_h_physical(block: array[qubit, 4]) -> None:
    addressable_rz_half_pi_physical(block)
    addressable_rx_half_pi_physical(block)
    addressable_rz_half_pi_physical(block)


@guppy
@no_type_check
def addressable_rz_half_pi_logical(block: array[qubit, 2]) -> None:
    rz(block[1], pi / 2)


@guppy
@no_type_check
def addressable_rz_half_pi_physical(block: array[qubit, 4]) -> None:
    zz_max(block[2], block[3])


@guppy
@no_type_check
def addressable_rx_half_pi_logical(block: array[qubit, 2]) -> None:
    rx(block[1], pi / 2)


@guppy
@no_type_check
def addressable_rx_half_pi_physical(block: array[qubit, 4]) -> None:
    h(block[0])
    h(block[2])
    zz_max(block[0], block[2])
    h(block[0])
    h(block[2])


@guppy
@no_type_check
def addressable_rx_minus_half_pi_logical(block: array[qubit, 2]) -> None:
    rx(block[1], -pi / 2)


@guppy
@no_type_check
def addressable_rx_minus_half_pi_physical(block: array[qubit, 4]) -> None:
    h(block[0])
    h(block[2])
    zz_phase(block[0], block[2], -pi / 2)
    h(block[0])
    h(block[2])


@guppy
@no_type_check
def double_h_logical(block: array[qubit, 2]) -> None:
    for i in range(2):
        h(block[i])


@guppy
@no_type_check
def double_h_physical(block: array[qubit, 4]) -> None:
    for i in range(4):
        h(block[i])
    mem_swap(block[1], block[2])


@guppy
@no_type_check
def interblock_zzmax_logical(
    first_block: array[qubit, 2],
    second_block: array[qubit, 2],
) -> None:
    zz_max(first_block[1], second_block[1])


@guppy
@no_type_check
def interblock_zzmax_physical(
    first_block: array[qubit, 4],
    second_block: array[qubit, 4],
) -> None:
    cx(first_block[2], second_block[2])
    cx(first_block[3], second_block[3])
    zz_max(second_block[2], second_block[3])
    cx(first_block[2], second_block[2])
    cx(first_block[3], second_block[3])


@guppy
@no_type_check
def transversal_cx_logical(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    for i in range(2):
        cx(first_block[i], second_block[i])


@guppy
@no_type_check
def transversal_cx_physical(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    for i in range(4):
        cx(first_block[i], second_block[i])


@guppy
@no_type_check
def logical_identity_double_block(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    pass


@guppy
@no_type_check
def physical_identity_double_block(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    pass


@guppy
@no_type_check
def non_ft_zero() -> array[qubit, 4]:
    block = array(qubit() for _ in range(4))
    h(block[2])
    cx(block[2], block[1])
    cx(block[2], block[3])
    cx(block[1], block[0])
    return block


@guppy
@no_type_check
def choi_state(
    unitary: Function[[array[qubit, 4]], None],
) -> tuple[array[qubit, 4], array[qubit, 4]]:
    control_block = non_ft_zero()
    target_block = non_ft_zero()

    double_h_physical(control_block)
    transversal_cx_physical(control_block, target_block)

    unitary(target_block)

    return control_block, target_block


@guppy
@no_type_check
def choi_state_double_block(
    unitary: Function[[array[qubit, 4], array[qubit, 4]], None],
) -> tuple[array[qubit, 4], array[qubit, 4], array[qubit, 4], array[qubit, 4]]:
    first_control_block = non_ft_zero()
    first_target_block = non_ft_zero()
    second_control_block = non_ft_zero()
    second_target_block = non_ft_zero()

    double_h_physical(first_control_block)
    double_h_physical(second_control_block)

    transversal_cx_physical(first_control_block, first_target_block)
    transversal_cx_physical(second_control_block, second_target_block)

    unitary(first_target_block, second_target_block)

    return (
        first_control_block,
        first_target_block,
        second_control_block,
        second_target_block,
    )


ICEBERG_4_2_2_GENERATORS = pauli.StringSet.from_cmpnts(
    pauli.Strings.from_str(
        "X0 X1 X2 X3, Z0 Z1 Z2 Z3",
        4,
    )
)

# IMPORTANT: Iceberg codeblock ordering

# [top q1, q2, bottom]

# ICEBERG_4_2_2_X[0]: XI -> XXII
# ICEBERG_4_2_2_X[1]: IX -> XIXI

ICEBERG_4_2_2_X = pauli.Strings.from_str(
    "X0 X1 I2 I3, X0 I1 X2 I3",
    4,
)

# ICEBERG_4_2_2_Z[0]: ZI -> IZIZ
# ICEBERG_4_2_2_Z[1]: IZ -> IIZZ

ICEBERG_4_2_2_Z = pauli.Strings.from_str(
    "I0 Z1 I2 Z3, I0 I1 Z2 Z3",
    4,
)


ICEBERG_4_2_2 = StabilizerCode(
    num_physical_qubits=4,
    num_logical_qubits=2,
    distance=2,
    generators=ICEBERG_4_2_2_GENERATORS,
    x_logicals=ICEBERG_4_2_2_X,
    z_logicals=ICEBERG_4_2_2_Z,
)
