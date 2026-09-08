"""Abstractions for code definitions."""

from __future__ import annotations

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
    generators: pauli.SignTermSet
    x_logicals: pauli.SignTerms
    z_logicals: pauli.SignTerms
    """Definition for a stabilizer code.


    .. code-block:: python

        from guppyft.code_def import StabilizerCode

        STEANE_DEF = StabilizerCode.from_python_strings(
        num_physical_qubits=7,
        num_logical_qubits=1,
        distance=3,
        generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
        x_logicals=["XXXXXXX"],
        z_logicals=["ZZZZZZZ"],
        )
    """

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

        strings: pauli.Strings = self.generators.into(pauli.Strings)
        all_stabilizer_generators_commute = np.all(strings.compatibility_matrix() == 1)

        if not all_stabilizer_generators_commute:
            raise CodeDefinitionError("All of the stabilizer generators must commute!")

    @staticmethod
    def from_python_strings(
        num_physical_qubits: int,
        num_logical_qubits: int,
        distance: int,
        generators: list[str],
        x_logicals: list[str],
        z_logicals: list[str],
    ) -> StabilizerCode:
        """Helper to create a StabilizerCode from lists of Python strings.

        The strings must be defined over the alphabet :math:`\\{I, X, Y, Z\\}` and
        must be of length equal to the number of physical qubits.
        A sign may be provided at the front. If a string is missing a sign,
        it is assumed to be positive.

        :param num_physical_qubits: The number of physical qubits in the code.
        :param num_logical_qubits: The number of logical qubits in the code.
        :param distance: The distance of the code.
        :param generators: A list of stabilizer generators as Pauli strings.
        :param x_logicals: A list of :math:`X` logical operators as Pauli strings.
        :param z_logicals: A list of :math:`Z` logical operators as Pauli strings.
        :return: A StabilizerCode instance representing the code.
        """
        zixy_generators = pauli.SignTermSet.from_iterable(
            (_str_to_zixy(s, num_physical_qubits) for s in generators),
            num_physical_qubits,
        )

        zixy_x_logicals = pauli.SignTerms.from_iterable(
            (_str_to_zixy(s, num_physical_qubits) for s in x_logicals),
            num_physical_qubits,
        )

        zixy_z_logicals = pauli.SignTerms.from_iterable(
            (_str_to_zixy(s, num_physical_qubits) for s in z_logicals),
            num_physical_qubits,
        )

        return StabilizerCode(
            num_physical_qubits=num_physical_qubits,
            num_logical_qubits=num_logical_qubits,
            distance=distance,
            generators=zixy_generators,
            x_logicals=zixy_x_logicals,
            z_logicals=zixy_z_logicals,
        )


def _str_to_zixy(s: str, n: int) -> pauli.SignTerm:
    if s[0] not in "+-":
        sign = "+"
    else:
        sign = s[0]
        s = s[1:]  # Drop the sign, since it is in a separate variable

    if len(s) != n:
        raise CodeDefinitionError(
            f"All Pauli strings must be of length {n}. "
            f"Got string '{s}' of length {len(s)}."
        )
    if not all(c in "IXYZ" for c in s):
        raise CodeDefinitionError(
            f"All Pauli strings must be defined over the alphabet {{I, X, Y, Z}}. "
            f"Got string '{s}' with invalid characters."
        )

    pauli_str = "".join(f"{c}{i} " for i, c in enumerate(s))
    return pauli.SignTerm.from_str(f"({sign}1, {pauli_str})", n)


def identity_code(k: int) -> StabilizerCode:
    """Return a stabilizer code that encodes :math:`k` logical qubits into
      :math`k` physical qubits. This is the trivial code with distance 1.

    :param k: The number of logical qubits to encode.
    :return: A StabilizerCode instance representing the identity code.
    """
    return StabilizerCode.from_python_strings(
        num_physical_qubits=k,
        num_logical_qubits=k,
        distance=1,
        generators=[],
        x_logicals=["I" * i + "X" + "I" * (k - i - 1) for i in range(k)],
        z_logicals=["I" * i + "Z" + "I" * (k - i - 1) for i in range(k)],
    )
