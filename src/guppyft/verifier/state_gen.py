from enum import Enum
from typing import no_type_check

from guppylang import guppy
from guppylang.std.quantum import qubit, x, z, h, s, sdg, cz, measure_array
from guppylang.std.builtins import array, comptime, result
from guppylang.defs import GuppyFunctionDefinition

from zixy.qubit import pauli
from zixy.qubit.clifford import GateList
from zixy._zixy import SymplecticPart

class SQClifford(Enum):
    I = 0
    H = 1
    S = 2

N = guppy.nat_var("N")

def gen_guppy_state_prep(
    tableau: pauli.SignTerms,
) -> GuppyFunctionDefinition[[], array[qubit, N]]:
    """Generate a guppy function that prepares a stabilizer state for the given
    tableau.

    The circuit is not fault tolerant. It is produced by converting the given
    stabilizer state into a graph state (using single qubit gates) and
    preparing the graph state using the sequence of CZ gates given by its
    adjacency matrix.

    :param tableau: A list of signed Pauli stabilizers.
    :return: A guppy function definition that prepares the state.
    """

    n_qubits = len(tableau.qubits)
    graph_tableau = tableau.clone()
    sq_gates = convert_to_graph_state(graph_tableau)

    @guppy.comptime
    @no_type_check
    def stabilizer_state_prep() -> array[qubit, comptime(n_qubits)]:

        # Initialise all qubits in the |+> state
        qs = array(qubit() for _ in range(n_qubits))
        for i in range(len(qs)):
            h(qs[i])

        for i, stabilizer in enumerate(graph_tableau):

            # Convert the X stabilizer of the |+> state on qs[i] to be
            # the Pauli string `stabilizer` by applying CZ gates.
            for q in range(i+1, n_qubits):
                # Only need to apply CZ for q > i; the Z before the i-th
                # position are guaranteed to be satisfied due to symmetric
                # property of the graph states tableau.
                if stabilizer.string[q] == pauli.Z:
                    cz(qs[i], qs[q])

            # To fix the sign, we make use of the fact that the i-th qubit on
            # `stabilizer` is guaranteed to be X, so we can flip the sign with Z
            if stabilizer.coeff.to_numeric() == -1:
                z(qs[i])

        # Apply the SQ gates to convert it to the target stabilizer state
        for q, gate in enumerate(sq_gates):
            match gate:
                case SQClifford.I:
                    pass
                case SQClifford.H:
                    h(qs[q])
                case SQClifford.S:
                    # Apply inverse since we want graph state -> target state
                    sdg(qs[q])

        return qs

    return stabilizer_state_prep


def convert_to_graph_state(tableau: pauli.SignTerms) -> list[SQClifford]:
    """Given a stabilizer tableau, returns a list of single qubit gates
    that convert it to a graph state, and the tableau of the resulting graph state.

    The tableau returned is guaranteed to have X only on the diagonal, and all
    other elements are either I or Z, forming a symmetric tableau.

    :param tableau: A list of signed Pauli stabilizers, modified in-place.
    :return: A list of single qubit gates that convert the input to a graph state.
    """

    all_q = list(range(len(tableau.qubits)))
    gates_to_apply = [SQClifford.I for _ in all_q]

    # Try to solve for X/Y everywhere
    tableau.canonicalize(
        mode_order = [(q, SymplecticPart.X) for q in all_q],
        to_solve = all_q,
        additional_reduces = [],
    )

    # Find out which qubits need a Hadamard applied to them
    remaining_strings = {s for s in range(len(tableau))}
    for q in all_q:
        matches = set()  # Identify all strings with an X or Y on qubit q
        for i in remaining_strings:
            if tableau[i].string[q] in (pauli.X, pauli.Y):
                matches.add(i)
        if len(matches) == 1:
            # This qubit is already solved for X/Y
            # Eliminate the corresponding string from the set since we don't
            # want any other qubit to use it as its X/Y representative.
            remaining_strings -= matches
        else:
            # This qubit is not solved for X/Y. Therefore, it must be possible
            # to solve it for Z. Apply a Hadamard to convert it to X/Y.
            gates_to_apply[q] = SQClifford.H
            tableau.conj_clifford_list(GateList().h(q))

    # Solve for X/Y everywhere. Now it is guaranteed to solve for all qubits.
    tableau.canonicalize(
        mode_order = [(q, SymplecticPart.X) for q in all_q],
        to_solve = all_q,
        additional_reduces = [],
    )

    # By now the tableau should have X/Y on the diagonal and I/Z elsewhere.
    # Convert any Y into X by applying S gates
    for q in all_q:
        if tableau[q].string[q] == pauli.Y:
            gates_to_apply[q] = SQClifford.S
            tableau.conj_clifford_list(GateList().s(q))
        assert tableau[q].string[q] == pauli.X

    return gates_to_apply