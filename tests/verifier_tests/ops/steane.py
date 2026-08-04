from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import cx, discard, h, measure, qubit, s, sdg
from zixy.qubit import pauli
from zixy.qubit.pauli import X, Z

from guppyft.verifier.code import StabilizerCode

STEANE_X_LOGICAL = pauli.String(7, (X, X, X, X, X, X, X))
STEANE_Z_LOGICAL = pauli.String(7, (Z, Z, Z, Z, Z, Z, Z))

# Stabilizer generators for Steane taken from Quantinuum/eris

# ZZZZIII -> 0, 1, 2, 3
# IZZIZZI -> 1, 2, 4, 5
# IIZZIZZ -> 2, 3, 5, 6

# Steane is self dual so the X stabilizers have the same indices.


STEANE_GENERATORS = pauli.StringSet.from_cmpnts(
    pauli.Strings.from_str(
        "X0 X1 X2 X3 I4 I5 I6, I0 X1 X2 I3 X4 X5 I6, I0 I1 X2 X3 I4 X5 X6, "
        "Z0 Z1 Z2 Z3 I4 I5 I6, I0 Z1 Z2 I3 Z4 Z5 I6, I0 I1 Z2 Z3 I4 Z5 Z6",
        7,
    )
)


STEANE_DEF = StabilizerCode(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=STEANE_GENERATORS,
    x_logicals=STEANE_X_LOGICAL.into(pauli.Strings),
    z_logicals=STEANE_Z_LOGICAL.into(pauli.Strings),
)


@guppy
@no_type_check
def specify_identity(block: array[qubit, 1]) -> None:
    pass


@guppy
@no_type_check
def specify_identity_with_shor_extraction(block: array[qubit, 1]) -> None:
    ancilla = qubit()
    discard(ancilla)


@guppy
@no_type_check
def specify_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


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
def specify_h_with_ancilla(block: array[qubit, 1]) -> None:
    ancilla = qubit()
    h(block[0])
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
