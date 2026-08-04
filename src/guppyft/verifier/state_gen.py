from enum import Enum
from typing import no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, comptime
from guppylang.std.quantum import cz, h, qubit, sdg, z
from zixy._zixy import SymplecticPart
from zixy.qubit import pauli
from zixy.qubit.clifford import GateList

from guppyft.verifier.code import StabilizerCode
from guppyft.verifier.expansion import get_expanded_stabilizer_set
from guppyft.verifier.utils import SingleBlockUnitary, array_slicer


class SQClifford(Enum):
    I = 0  # noqa: E741
    H = 1
    S = 2


N = guppy.nat_var("N")


def gen_guppy_state_prep(
    tableau: pauli.SignTerms,
) -> GuppyFunctionDefinition[[], array[qubit, N]]:  # type: ignore[valid-type]
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
            for q in range(i + 1, n_qubits):
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

    return stabilizer_state_prep  # type: ignore[no-any-return]


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
        mode_order=[(q, SymplecticPart.X) for q in all_q],
        to_solve=all_q,
        additional_reduces=[],
    )

    # Find out which qubits need a Hadamard applied to them
    h_gates = GateList()
    current_string = 0
    for q in range(len(tableau.qubits)):
        term = tableau[current_string]
        assert isinstance(term, pauli.SignTerm)
        if term.string[q] in (pauli.X, pauli.Y):
            # This qubit is already solved for X/Y. It is guaranteed that
            # none of the other Pauli strings will have an X/Y on `q`
            current_string += 1
        else:
            # Since `canonicalize` guarantees the `mode_order`, if `q` was
            # solvable for X/Y, it would have been found here.
            # Since it is not solvable for X/Y, it must solvable for Z.
            # Apply a Hadamard to convert it to solvable for X.
            gates_to_apply[q] = SQClifford.H
            h_gates.h(q)
    tableau.conj_clifford_list(h_gates)

    # Solve for X/Y everywhere. Now it is guaranteed to solve for all qubits.
    tableau.canonicalize(
        mode_order=[(q, SymplecticPart.X) for q in all_q],
        to_solve=all_q,
        additional_reduces=[],
    )

    # By now the tableau should have X/Y on the diagonal and I/Z elsewhere.
    # Convert any Y into X by applying S gates
    s_gates = GateList()
    for q in all_q:
        term = tableau[q]
        assert isinstance(term, pauli.SignTerm)
        if term.string[q] == pauli.Y:
            gates_to_apply[q] = SQClifford.S
            s_gates.s(q)
    tableau.conj_clifford_list(s_gates)

    return gates_to_apply


TWICE_NUM_BLOCKS = guppy.nat_var("TWICE_NUM_BLOCKS")


def gen_choi_state(
    code: StabilizerCode,
    clifford_func: SingleBlockUnitary,
    n_blocks: int,
) -> GuppyFunctionDefinition[[], array[array[qubit, N], TWICE_NUM_BLOCKS]]:  # type: ignore[valid-type]
    """Generate a Guppy function that prepares the Choi state of a single block
    Clifford unitary.

    :param code: The stabilizer code.
    :param clifford_func: A Guppy function which implements a Clifford unitary
        on a single code block.
    :param n_blocks: The number of code blocks that the Clifford function
        acts on.
    :return: A Guppy function definition that prepares the Choi state on
        `2*n_blocks` blocks.
    """

    k = code.num_logical_qubits
    # First, produce the tableau of `k*n_blocks` Bell pairs
    # The qubits are arranged in groups of size `k`:
    #   (block0_input, block0_output, block1_input, block1_output, ...)
    # Each Bell pair entangles the i-th qubits of blockj_input with blockj_output
    unencoded_bell_bundle = pauli.SignTerms(2 * k * n_blocks)
    for j in range(n_blocks):
        for i in range(k):
            # The stabilizers of the i-th Bell pair of block j are:
            unencoded_bell_bundle.append(
                pauli.SignTerm(
                    2 * k * n_blocks,
                    {2 * j * k + i: pauli.X, (2 * j + 1) * k + i: pauli.X},
                )
            )
            unencoded_bell_bundle.append(
                pauli.SignTerm(
                    2 * k * n_blocks,
                    {2 * j * k + i: pauli.Z, (2 * j + 1) * k + i: pauli.Z},
                )
            )

    # Extend the tableau to physical qubits
    encoded_bell_bundle = get_expanded_stabilizer_set(
        unencoded_bell_bundle, code, n_blocks
    )

    # Generate the Guppy function that prepares the bundle of encoded Bell states
    prep_func = gen_guppy_state_prep(encoded_bell_bundle)

    # Slice array and apply the clifford_func to the target block
    match n_blocks:
        case 1:

            @guppy
            @no_type_check
            def choi_prep[N: nat]() -> array[array[qubit, N], 2]:
                # Prepare the Bell states
                qs = prep_func()

                # Slice into blocks
                slicer = array_slicer(qs)
                input_leg = slicer.take(comptime(N))
                output_leg = slicer.take(comptime(N))
                slicer.discard_empty()

                # Apply the Clifford unitary to the output leg
                clifford_func(output_leg)

                return array(input_leg, output_leg)

        case 2:

            @guppy
            @no_type_check
            def choi_prep[N: nat]() -> array[array[qubit, N], 4]:
                # Prepare the Bell states
                qs = prep_func()

                # Slice into blocks
                slicer = array_slicer(qs)
                input0_leg = slicer.take(comptime(N))
                output0_leg = slicer.take(comptime(N))
                input1_leg = slicer.take(comptime(N))
                output1_leg = slicer.take(comptime(N))
                slicer.discard_empty()

                # Apply the Clifford unitary to the output legs
                clifford_func(output0_leg, output1_leg)

                return array(input0_leg, output0_leg, input1_leg, output1_leg)

        case _:
            raise NotImplementedError(
                f"Currently only 1 or 2 code blocks are supported. Got {n_blocks=}."
            )

    return choi_prep  # type: ignore[no-any-return]
