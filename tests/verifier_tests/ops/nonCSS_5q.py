# Non-CSS [[5,1,3]] code from
#   "Universal Fault-Tolerant Gates on Concatenated Stabilizer Codes"
#       https://journals.aps.org/prx/pdf/10.1103/PhysRevX.6.031039

from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.mem import mem_swap
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg, y, z
from zixy.qubit import pauli
from zixy.qubit.pauli import X, Z

from guppyft.verifier.code import StabilizerCode

X_LOGICAL = pauli.String(5, (X, X, X, X, X))
Z_LOGICAL = pauli.String(5, (Z, Z, Z, Z, Z))


GENERATORS = pauli.StringSet.from_cmpnts(
    pauli.Strings.from_str(
        "Z0 Z1 X2 I3 X4, X0 Z1 Z2 X3 I4, I0 X1 Z2 Z3 X4, X0 I1 X2 Z3 Z4",
        5,
    )
)


CODE_DEF = StabilizerCode(
    num_physical_qubits=5,
    num_logical_qubits=1,
    distance=3,
    generators=GENERATORS,
    x_logicals=X_LOGICAL.into(pauli.Strings),
    z_logicals=Z_LOGICAL.into(pauli.Strings),
)


@guppy
@no_type_check
def specify_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def specify_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def implement_identity(block: array[qubit, 5]) -> None:
    pass


@guppy
@no_type_check
def implement_identity_double_block(
    first_block: array[qubit, 5], second_block: array[qubit, 5]
) -> None:
    pass


@guppy
@no_type_check
def specify_zero_state() -> array[qubit, 1]:
    return array(qubit())


@guppy
@no_type_check
def implement_non_ft_zero_state() -> array[qubit, 5]:
    """Non fault-tolerant zero state preparation.

    Not taken from any reference, derived in blackboard.
    """
    block = array(qubit() for _ in range(5))

    for i in range(len(block)):
        h(block[i])

    minus_ids = array(0, 3)
    for i in minus_ids:
        z(block[i])

    cz_pairs = array((0, 2), (0, 4), (1, 2), (1, 3), (1, 4), (2, 4), (3, 4))
    for i, j in cz_pairs:
        cz(block[i], block[j])

    h(block[4])

    return block


@guppy
@no_type_check
def specify_plus_state() -> array[qubit, 1]:
    q = qubit()
    h(q)
    return array(q)


@guppy
@no_type_check
def implement_non_ft_plus_state() -> array[qubit, 5]:
    block = implement_non_ft_zero_state()
    implement_h(block)
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
def implement_non_ft_bell_state() -> tuple[array[qubit, 5], array[qubit, 5]]:
    block0 = implement_non_ft_plus_state()
    block1 = implement_non_ft_zero_state()
    implement_cx(block0, block1)
    return block0, block1


@guppy
@no_type_check
def specify_k(block: array[qubit, 1]) -> None:
    h(block[0])
    s(block[0])


@guppy
@no_type_check
def implement_k(block: array[qubit, 5]) -> None:
    """Fig 2(a)"""
    for i in range(len(block)):
        h(block[i])
        s(block[i])


@guppy
@no_type_check
def specify_kdg(block: array[qubit, 1]) -> None:
    sdg(block[0])
    h(block[0])


@guppy
@no_type_check
def implement_kdg(block: array[qubit, 5]) -> None:
    """Dagger of Fig 2(a)"""
    for i in range(len(block)):
        sdg(block[i])
        h(block[i])


@guppy
@no_type_check
def specify_h(block: array[qubit, 1]) -> None:
    h(block[0])


@guppy
@no_type_check
def implement_h(block: array[qubit, 5]) -> None:
    """Fig 2(b)"""
    for i in range(len(block)):
        h(block[i])
    mem_swap(block[1], block[0])  # block[0] now contains the correct qubit
    mem_swap(block[3], block[4])  # block[4] now contains the correct qubit
    mem_swap(block[1], block[3])


@guppy
@no_type_check
def specify_cz(first_block: array[qubit, 1], second_block: array[qubit, 1]) -> None:
    cz(first_block[0], second_block[0])


@guppy
@no_type_check
def implement_cz(first_block: array[qubit, 5], second_block: array[qubit, 5]) -> None:
    """Fig 3"""

    h(first_block[0])
    s(first_block[0])
    y(first_block[2])
    h(first_block[4])
    s(first_block[4])
    h(second_block[0])
    s(second_block[0])
    y(second_block[2])
    h(second_block[4])
    s(second_block[4])

    cz_pairs = array(
        # Fig 3(a)
        (0, 0),
        (2, 2),
        (4, 4),
        (0, 4),
        (2, 0),
        (4, 2),
        # Fig 3(b)
        (0, 2),
        (2, 4),
        (4, 0),
    )
    for i, j in cz_pairs:
        cz(first_block[i], second_block[j])

    sdg(first_block[0])
    h(first_block[0])
    y(first_block[2])
    sdg(first_block[4])
    h(first_block[4])
    sdg(second_block[0])
    h(second_block[0])
    y(second_block[2])
    sdg(second_block[4])
    h(second_block[4])


@guppy
@no_type_check
def specify_cx(first_block: array[qubit, 1], second_block: array[qubit, 1]) -> None:
    cx(first_block[0], second_block[0])


@guppy
@no_type_check
def implement_cx(first_block: array[qubit, 5], second_block: array[qubit, 5]) -> None:
    """Construct by composition"""
    implement_h(second_block)
    implement_cz(first_block, second_block)
    implement_h(second_block)
