from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import cx, h, qubit, x
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode

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


@guppy
@no_type_check
def specify_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def implement_identity(block: array[qubit, 3]) -> None:
    pass


@guppy
@no_type_check
def specify_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def implement_identity_double_block(
    first_block: array[qubit, 3], second_block: array[qubit, 3]
) -> None:
    pass


@guppy
@no_type_check
def specify_zero_state() -> array[qubit, 1]:
    return array(qubit())


@guppy
@no_type_check
def implement_non_ft_zero_state() -> array[qubit, 3]:
    """Non fault-tolerant zero state preparation."""
    return array(qubit() for _ in range(3))


@guppy
@no_type_check
def specify_plus_state() -> array[qubit, 1]:
    q = qubit()
    h(q)
    return array(q)


@guppy
@no_type_check
def implement_non_ft_plus_state() -> array[qubit, 3]:
    block = array(qubit() for _ in range(3))

    h(block[0])
    cx(block[0], block[1])
    cx(block[0], block[2])

    return block


@guppy
@no_type_check
def specify_bell_state() -> tuple[array[qubit, 1], array[qubit, 1]]:
    q0 = qubit()
    q1 = qubit()
    h(q0)
    cx(q0, q1)
    return array(q0), array(q1)


@guppy
@no_type_check
def implement_non_ft_bell_state() -> tuple[array[qubit, 3], array[qubit, 3]]:
    block0 = implement_non_ft_plus_state()
    block1 = implement_non_ft_zero_state()
    implement_cx(block0, block1)
    return block0, block1


@guppy
@no_type_check
def specify_x(block: array[qubit, 1]) -> None:
    x(block[0])


@guppy
@no_type_check
def implement_x(block: array[qubit, 3]) -> None:
    for i in range(len(block)):
        x(block[i])


@guppy
@no_type_check
def specify_cx(control_block: array[qubit, 1], target_block: array[qubit, 1]) -> None:
    cx(control_block[0], target_block[0])


@guppy
@no_type_check
def implement_cx(control_block: array[qubit, 3], target_block: array[qubit, 3]) -> None:
    for i in range(len(control_block)):
        cx(control_block[i], target_block[i])
