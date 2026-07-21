# Non-CSS [[5,1,3]] code from
#   "Universal Fault-Tolerant Gates on Concatenated Stabilizer Codes"
#       https://journals.aps.org/prx/pdf/10.1103/PhysRevX.6.031039

from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.mem import mem_swap
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg, y
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
def logical_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def logical_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def physical_identity(block: array[qubit, 5]) -> None:
    pass


@guppy
@no_type_check
def physical_identity_double_block(
    first_block: array[qubit, 5], second_block: array[qubit, 5]
) -> None:
    pass


@guppy
@no_type_check
def logical_k(block: array[qubit, 1]) -> None:
    h(block[0])
    s(block[0])


@guppy
@no_type_check
def physical_k(block: array[qubit, 5]) -> None:
    """Fig 2(a)"""
    for i in range(len(block)):
        h(block[i])
        s(block[i])


@guppy
@no_type_check
def logical_kdg(block: array[qubit, 1]) -> None:
    sdg(block[0])
    h(block[0])


@guppy
@no_type_check
def physical_kdg(block: array[qubit, 5]) -> None:
    """Dagger of Fig 2(a)"""
    for i in range(len(block)):
        sdg(block[i])
        h(block[i])


@guppy
@no_type_check
def logical_h(block: array[qubit, 1]) -> None:
    h(block[0])


@guppy
@no_type_check
def physical_h(block: array[qubit, 5]) -> None:
    """Fig 2(b)"""
    for i in range(len(block)):
        h(block[i])
    mem_swap(block[1], block[0])  # block[0] now contains the correct qubit
    mem_swap(block[3], block[4])  # block[4] now contains the correct qubit
    mem_swap(block[1], block[3])


@guppy
@no_type_check
def logical_cz(first_block: array[qubit, 1], second_block: array[qubit, 1]) -> None:
    cz(first_block[0], second_block[0])


@guppy
@no_type_check
def physical_cz(first_block: array[qubit, 5], second_block: array[qubit, 5]) -> None:
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
def logical_cx(first_block: array[qubit, 1], second_block: array[qubit, 1]) -> None:
    cx(first_block[0], second_block[0])


@guppy
@no_type_check
def physical_cx(first_block: array[qubit, 5], second_block: array[qubit, 5]) -> None:
    """Construct by composition"""
    physical_h(second_block)
    physical_cz(first_block, second_block)
    physical_h(second_block)
