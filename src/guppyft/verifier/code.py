import functools
from dataclasses import dataclass

import numpy as np
from zixy.container.coeffs import ComplexSign
from zixy.qubit import pauli
from zixy.qubit.pauli import X, Z

from guppyft.verifier.utils import string_to_strings


class CodeDefinitionError(ValueError):
    """Raised when the definition of a stabilizer code is invalid."""


@dataclass(frozen=True)
class StabilizerCode:
    num_physical_qubits: int
    num_logical_qubits: int
    distance: int
    generators: pauli.StringSet
    x_logicals: pauli.Strings
    z_logicals: pauli.Strings

    @functools.cached_property
    def y_logicals(self) -> pauli.ComplexSignTerms:
        terms = pauli.ComplexSignTerms(self.num_physical_qubits)
        for j in range(self.num_logical_qubits):
            y_term = self.x_logicals[j] * self.z_logicals[j]
            # ComplexSign(k) ~ i^k
            # y_logicals[j] = i * (x_logicals[j] * z_logicals[j])
            y_logical_cmpt = ComplexSign(1) * y_term
            terms.append(y_logical_cmpt)
        return terms

    def __post_init__(self) -> None:
        if len(self.generators) != self.num_physical_qubits - self.num_logical_qubits:
            raise CodeDefinitionError(
                "The number of stabilizer generators must equal n-k."
                + f" Got n={self.num_physical_qubits}, "
                + f"k={self.num_logical_qubits} with {len(self.generators)} generators."
            )

        if len(self.x_logicals) != self.num_logical_qubits:
            raise CodeDefinitionError(
                "Incorrect number of X logical operators: "
                f"expected {self.num_logical_qubits}, "
                f"got {len(self.x_logicals)}."
            )

        if len(self.z_logicals) != self.num_logical_qubits:
            raise CodeDefinitionError(
                "Incorrect number of Z logical operators: "
                f"expected {self.num_logical_qubits}, "
                f"got {len(self.z_logicals)}."
            )

        all_stabilizer_generators_commute = (
            np.all(self.generators.to_strings().compatibility_matrix()) == 1
        )

        if not all_stabilizer_generators_commute:
            raise CodeDefinitionError("All of the stabilizer generators must commute!")


STEANE_X_LOGICAL = pauli.String(7, (X, X, X, X, X, X, X))
STEANE_Z_LOGICAL = pauli.String(7, (Z, Z, Z, Z, Z, Z, Z))

# Stabilizer generators for Steane taken from Quantinuum/eris

# ZZZZIII -> 0, 1, 2, 3
# IZZIZZI -> 1, 2, 4, 5
# IIZZIZZ -> 2, 3, 5, 6

# Steane is self dual so the X stabilizers have the same indices.


STEANE_STABILIZER_GENERATORS = pauli.StringSet.from_strings(
    pauli.Strings.from_str(
        "X0 X1 X2 X3 I4 I5 I6, I0 X1 X2 I3 X4 X5 I6, I0 I1 X2 X3 I4 X5 X6, "
        "Z0 Z1 Z2 Z3 I4 I5 I6, I0 Z1 Z2 I3 Z4 Z5 I6, I0 I1 Z2 Z3 I4 Z5 Z6",
        7,
    )
)


STEANE = StabilizerCode(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=STEANE_STABILIZER_GENERATORS,
    x_logicals=string_to_strings(STEANE_X_LOGICAL),
    z_logicals=string_to_strings(STEANE_Z_LOGICAL),
)

BIT_FLIP_CODE_GENERATORS = pauli.StringSet.from_strings(
    pauli.Strings.from_str("Z0 Z1, Z1 Z2", 3)
)

BIT_FLIP_CODE = StabilizerCode(
    num_physical_qubits=3,
    num_logical_qubits=1,
    distance=1,
    generators=BIT_FLIP_CODE_GENERATORS,
    x_logicals=string_to_strings(pauli.String.from_str("X0 X1 X2")),
    z_logicals=string_to_strings(pauli.String.from_str("Z0 I1 I2")),
)


ICEBERG_4_2_2_GENERATORS = pauli.StringSet.from_strings(
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
