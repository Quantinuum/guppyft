from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import cx, discard, h, measure, measure_array, qubit, s, sdg

from guppyft.verifier.code import StabilizerCode

STEANE_DEF = StabilizerCode.from_strings(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
    x_logicals=["XXXXXXX"],
    z_logicals=["ZZZZZZZ"],
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
def specify_zero_state() -> array[qubit, 1]:
    return array(qubit())


@guppy
@no_type_check
def implement_non_ft_zero_state() -> array[qubit, 7]:
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
def implement_ft_zero_state() -> array[qubit, 7]:
    """Dummy fault-tolerant zero state preparation.

    Fig 1b from https://www.nature.com/articles/srep19578
    """
    block = implement_non_ft_zero_state()
    ancilla = implement_non_ft_zero_state()

    # Perform Steane-style flagging. This is very wasteful, but simple.
    implement_cx(block, ancilla)
    measure_array(ancilla)
    # For proper FT implementation, we would need to check that the XORing
    # that determines the Z stabilizer information is correct.

    return block


@guppy
@no_type_check
def specify_plus_state() -> array[qubit, 1]:
    q = qubit()
    h(q)
    return array(q)


@guppy
@no_type_check
def implement_non_ft_plus_state() -> array[qubit, 7]:
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
def implement_non_ft_bell_state() -> tuple[array[qubit, 7], array[qubit, 7]]:
    block0 = implement_non_ft_zero_state()
    block1 = implement_non_ft_zero_state()
    implement_h(block0)
    implement_cx(block0, block1)
    return block0, block1


@guppy
@no_type_check
def implement_identity(block: array[qubit, 7]) -> None:
    pass


@guppy
@no_type_check
def implement_identity_with_shor_extraction(block: array[qubit, 7]) -> None:
    # measure the ZZZZIII stabilizer
    ancilla = qubit()
    for i in array(0, 1, 2, 3):
        cx(block[i], ancilla)
    measure(ancilla)


@guppy
@no_type_check
def implement_identity_double_block(
    first_block: array[qubit, 7], second_block: array[qubit, 7]
) -> None:
    pass


@guppy
@no_type_check
def implement_identity_double_block_with_shor_extraction(
    first_block: array[qubit, 7], second_block: array[qubit, 7]
) -> None:
    first_ancilla, second_ancilla = qubit(), qubit()
    for i in array(0, 1, 2, 3):
        cx(first_block[i], first_ancilla)
        cx(second_block[i], second_ancilla)

    measure(first_ancilla)
    measure(second_ancilla)


@guppy
@no_type_check
def implement_h(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        h(block[i])


@guppy
@no_type_check
def specify_h(block: array[qubit, 1]) -> None:
    h(block[0])


@guppy
@no_type_check
def implement_h_with_ancilla(block: array[qubit, 7]) -> None:
    ancilla = qubit()
    for i in range(len(block)):
        h(block[i])
    discard(ancilla)


@guppy
@no_type_check
def specify_s(block: array[qubit, 1]) -> None:
    s(block[0])


@guppy
@no_type_check
def implement_s(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        sdg(block[i])


@guppy
@no_type_check
def specify_sdg(block: array[qubit, 1]) -> None:
    sdg(block[0])


@guppy
@no_type_check
def implement_sdg(block: array[qubit, 7]) -> None:
    for i in range(len(block)):
        s(block[i])


@guppy
@no_type_check
def specify_cx(first_block: array[qubit, 1], second_block: array[qubit, 1]) -> None:
    cx(first_block[0], second_block[0])


@guppy
@no_type_check
def implement_cx(first_block: array[qubit, 7], second_block: array[qubit, 7]) -> None:
    for i in range(len(first_block)):
        cx(first_block[i], second_block[i])
