from typing import no_type_check

from guppylang import guppy
from guppylang.std.array import array
from guppylang.std.quantum import qubit
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode


@guppy
@no_type_check
def logical_identity_double_block(
    first_block: array[qubit, 1], second_block: array[qubit, 1]
) -> None:
    pass


@guppy
@no_type_check
def physical_identity_double_block(
    first_block: array[qubit, 3], second_block: array[qubit, 3]
) -> None:
    pass


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
