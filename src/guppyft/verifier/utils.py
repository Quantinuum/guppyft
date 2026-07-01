from selene_stim_plugin.state import Pauli, Phase, Stabilizer, StabilizerList
from zixy.container.coeffs import Sign
from zixy.qubit import pauli


def _convert_pauli(selene_pauli: Pauli) -> pauli.PauliMatrix:
    "Convert a selene_stim_plugin.state.Pauli to a zixy.qubit.pauli.PauliMatrix."
    match selene_pauli:
        case selene_pauli.X:
            return pauli.PauliMatrix.X
        case selene_pauli.Y:
            return pauli.PauliMatrix.Y
        case selene_pauli.Z:
            return pauli.PauliMatrix.Z
        case selene_pauli.I:
            return pauli.PauliMatrix.I


def _get_real_phase(selene_phase: Phase) -> Sign:
    "Convert a selene Pauli phase to zixy. Phase must be real valued."
    match selene_phase:
        case Phase.REAL_POSITIVE:
            return Sign(0)
        case Phase.REAL_NEGATIVE:
            return Sign(1)
        case _:
            raise ValueError(
                f"The phase of a SignTerm must be real! Got {selene_phase}"
            )


def selene_stabilizer_to_zixy_signterm(stabilizer: Stabilizer) -> pauli.SignTerm:
    """Convert a selene_stim_plugin.state.Stabilizer to a zixy.qubit.pauli.SignTerm.

    :param stabilizer: A signed pauli Stabilizer in Selene's representation.
    :return: A Zixy SignTerms instance.
    """
    zixy_paulis: tuple[pauli.PauliMatrix, ...] = tuple(
        [_convert_pauli(p) for p in stabilizer.paulis]
    )
    term = pauli.SignTerm(len(zixy_paulis), zixy_paulis)
    signed_phase = _get_real_phase(stabilizer.phase)
    term.coeff = signed_phase
    return term


def stabilizerlist_to_signterms(stab_list: StabilizerList) -> pauli.SignTerms:
    """Convert a list of signed Pauli stablizers to zixy's representation.

    :param stab_list: A list of stabilizer's in Selene's representation.
    :return: a zixy SignTerms instance equivalent to stab_list.
    """
    sign_terms = pauli.SignTerms(qubits=len(stab_list.generators[0].paulis))
    for gen in stab_list.generators:
        term = selene_stabilizer_to_zixy_signterm(gen)
        sign_terms.append(term)
    return sign_terms


def stringset_to_signterms(
    string_set: pauli.StringSet, qubit_capacity: int
) -> pauli.SignTerms:
    """Utils function for converting a StringSet to an eqivalent SignTerms instance."""
    terms = pauli.SignTerms(qubits=qubit_capacity)
    for string in string_set.to_strings():
        terms.append(pauli.SignTerm.from_cmpnt_coeff(string, Sign(0)))
    return terms


def string_to_strings(string: pauli.String) -> pauli.Strings:
    """Convert a String instance to a Strings of unit length."""
    my_tuple = (string.get_tuple(),)
    return pauli.Strings.from_iterable(my_tuple, len(my_tuple[0]))
