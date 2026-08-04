# Non-CSS [[4,2,2]] code from
# "Simple logical quantum computation with concatenated symplectic double codes"
#   https://arxiv.org/pdf/2510.18753v1

from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.mem import mem_swap
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode


@guppy
@no_type_check
def logical_identity(block: array[qubit, 2]) -> None:
    pass


@guppy
@no_type_check
def logical_identity_double_block(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    pass


@guppy
@no_type_check
def physical_identity(block: array[qubit, 4]) -> None:
    pass


@guppy
@no_type_check
def physical_identity_double_block(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    pass


@guppy
@no_type_check
def logical_row1(block: array[qubit, 2]) -> None:
    """Table 2, row 1"""
    h(block[0])
    h(block[1])
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def physical_row1(block: array[qubit, 4]) -> None:
    """Table 2, row 1"""
    h(block[2])
    h(block[3])
    mem_swap(block[2], block[3])


@guppy
@no_type_check
def logical_row2(block: array[qubit, 2]) -> None:
    """Table 2, row 2"""
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def physical_row2(block: array[qubit, 4]) -> None:
    """Table 2, row 2"""
    for i in range(len(block)):
        h(block[i])


@guppy
@no_type_check
def logical_row3(block: array[qubit, 2]) -> None:
    """Table 2, row 3"""
    h(block[0])
    h(block[1])
    mem_swap(block[0], block[1])
    # U = C(X, X) = HH * CZ * HH
    h(block[0])
    h(block[1])
    cz(block[0], block[1])
    h(block[0])
    h(block[1])


@guppy
@no_type_check
def physical_row3(block: array[qubit, 4]) -> None:
    """Table 2, row 3"""
    h(block[1])
    h(block[3])
    mem_swap(block[2], block[3])
    mem_swap(block[1], block[3])


@guppy
@no_type_check
def logical_row4(block: array[qubit, 2]) -> None:
    """Table 2, row 4"""
    cx(block[0], block[1])
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def physical_row4_incorrect(block: array[qubit, 4]) -> None:
    """Table 2, row 4.

    This implementation is incorrect. It acts at it should on stabilizers and
    logicals except on logical Z1 which is sent to -Z0Z1 instead of +Z0Z1.
    """
    h(block[0])
    s(block[0])
    sdg(block[1])
    h(block[1])
    sdg(block[2])
    h(block[2])
    h(block[3])
    s(block[3])


@guppy
@no_type_check
def physical_row4_correct(block: array[qubit, 4]) -> None:
    """Correct implementation of Table 2, row 4."""
    h(block[0])
    sdg(block[0])
    sdg(block[1])
    h(block[1])
    s(block[2])
    h(block[2])
    h(block[3])
    s(block[3])


@guppy
@no_type_check
def logical_intra_cz(block: array[qubit, 2]) -> None:
    cz(block[0], block[1])


@guppy
@no_type_check
def physical_intra_cz(block: array[qubit, 4]) -> None:
    """Derived by combining Table2's rows 1,2,3"""
    mem_swap(block[1], block[2])


Z_LOGICAL = pauli.Strings.from_str(
    "I0 Z1 Z2 I3, Z0 I1 I2 Z3",
    4,
)
X_LOGICAL = pauli.Strings.from_str(
    "Z0 I1 X2 I3, I0 Z1 I2 X3",
    4,
)


GENERATORS = pauli.StringSet.from_cmpnts(
    pauli.Strings.from_str(
        "X0 Z1 Z2 X3, Z0 X1 X2 Z3",
        4,
    )
)


CODE_DEF = StabilizerCode(
    num_physical_qubits=4,
    num_logical_qubits=2,
    distance=2,
    generators=GENERATORS,
    x_logicals=X_LOGICAL,
    z_logicals=Z_LOGICAL,
)
