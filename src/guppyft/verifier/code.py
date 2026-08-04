from dataclasses import dataclass
from functools import cached_property

import numpy as np
from zixy.container.coeffs import ComplexSign
from zixy.qubit import pauli


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

    @cached_property
    def y_logicals(self) -> pauli.SignTerms:
        terms = pauli.ComplexSignTerms(self.num_physical_qubits)
        for j in range(self.num_logical_qubits):
            # ComplexSign(k) ~ i^k
            # y_logicals[j] = i * (x_logicals[j] * z_logicals[j])
            # y_term will always have a real (+/-)1 coefficient.
            y_term = ComplexSign(1) * (self.x_logicals[j] * self.z_logicals[j])
            terms.append(y_term)
        return terms.into(pauli.SignTerms)

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

        all_stabilizer_generators_commute = np.all(
            self.generators.to_strings().into(pauli.Strings).compatibility_matrix() == 1
        )

        if not all_stabilizer_generators_commute:
            raise CodeDefinitionError("All of the stabilizer generators must commute!")


def identity_code(k: int) -> StabilizerCode:
    """Return a stabilizer code that encodes k logical qubits into k physical qubits.
      This is the trivial code with distance 1.

    :param k: The number of logical qubits to encode.
    :return: A StabilizerCode instance representing the identity code.
    """
    x_logicals = pauli.Strings(k)
    z_logicals = pauli.Strings(k)
    for i in range(k):
        x_logicals.append(pauli.String(k, {i: pauli.X}))
        z_logicals.append(pauli.String(k, {i: pauli.Z}))

    return StabilizerCode(
        num_physical_qubits=k,
        num_logical_qubits=k,
        distance=1,
        generators=pauli.StringSet(k),  # No stabilizers
        x_logicals=x_logicals,
        z_logicals=z_logicals,
    )
