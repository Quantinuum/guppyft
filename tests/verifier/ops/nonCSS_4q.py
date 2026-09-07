# Non-CSS [[4,2,2]] code from
# "Simple logical quantum computation with concatenated symplectic double codes"
#   https://arxiv.org/pdf/2510.18753v1

from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.mem import mem_swap
from guppylang.std.quantum import cx, cz, h, qubit, s, sdg

from guppyft.code_def import StabilizerCode

CODE_DEF = StabilizerCode.from_python_strings(
    num_physical_qubits=4,
    num_logical_qubits=2,
    distance=2,
    generators=["XZZX", "ZXXZ"],
    x_logicals=["ZIXI", "IZIX"],
    z_logicals=["IZZI", "ZIIZ"],
)


@guppy
@no_type_check
def specify_identity(block: array[qubit, 2]) -> None:
    pass


@guppy
@no_type_check
def specify_identity_double_block(
    first_block: array[qubit, 2], second_block: array[qubit, 2]
) -> None:
    pass


@guppy
@no_type_check
def implement_identity(block: array[qubit, 4]) -> None:
    pass


@guppy
@no_type_check
def implement_identity_double_block(
    first_block: array[qubit, 4], second_block: array[qubit, 4]
) -> None:
    pass


@guppy
@no_type_check
def specify_zero_state() -> array[qubit, 2]:
    return array(qubit() for _ in range(2))


@guppy
@no_type_check
def implement_non_ft_zero_state() -> array[qubit, 4]:
    """Non fault-tolerant zero state preparation.

    Not taken from any reference, derived in blackboard.
    """
    block = array(qubit() for _ in range(4))

    h(block[0])
    h(block[1])
    cz(block[0], block[2])
    cz(block[1], block[3])
    cx(block[1], block[2])
    cx(block[0], block[3])

    return block


@guppy
@no_type_check
def specify_plus_state() -> array[qubit, 2]:
    qs = array(qubit() for _ in range(2))
    for i in range(len(qs)):
        h(qs[i])
    return qs


@guppy
@no_type_check
def implement_non_ft_plus_state() -> array[qubit, 4]:
    block = implement_non_ft_zero_state()
    implement_row1(block)
    return block


@guppy
@no_type_check
def specify_row1(block: array[qubit, 2]) -> None:
    """Table 2, row 1"""
    h(block[0])
    h(block[1])
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def implement_row1(block: array[qubit, 4]) -> None:
    """Table 2, row 1"""
    h(block[2])
    h(block[3])
    mem_swap(block[2], block[3])


@guppy
@no_type_check
def specify_row2(block: array[qubit, 2]) -> None:
    """Table 2, row 2"""
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def implement_row2(block: array[qubit, 4]) -> None:
    """Table 2, row 2"""
    for i in range(len(block)):
        h(block[i])


@guppy
@no_type_check
def specify_row3(block: array[qubit, 2]) -> None:
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
def implement_row3(block: array[qubit, 4]) -> None:
    """Table 2, row 3"""
    h(block[1])
    h(block[3])
    mem_swap(block[2], block[3])
    mem_swap(block[1], block[3])


@guppy
@no_type_check
def specify_row4(block: array[qubit, 2]) -> None:
    """Table 2, row 4"""
    cx(block[0], block[1])
    mem_swap(block[0], block[1])


@guppy
@no_type_check
def implement_row4_incorrect(block: array[qubit, 4]) -> None:
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
def implement_row4_correct(block: array[qubit, 4]) -> None:
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
def specify_intra_cz(block: array[qubit, 2]) -> None:
    cz(block[0], block[1])


@guppy
@no_type_check
def implement_intra_cz(block: array[qubit, 4]) -> None:
    """Derived by combining Table2's rows 1,2,3"""
    mem_swap(block[1], block[2])
