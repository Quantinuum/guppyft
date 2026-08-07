from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.builtins import array, comptime
from guppylang.std.debug import state_output
from guppylang.std.qsystem.random import RNG
from guppylang.std.quantum import cx, discard_array, h, qubit, s, sdg, x, y, z
from zixy.qubit import pauli

from guppyft.verifier.state_gen import (
    SQClifford,
    convert_to_graph_state,
    gen_guppy_state_prep,
)
from guppyft.verifier.utils import (
    stabilizerlist_to_signterms,
)
from guppyft.verifier.verify import _invoke_selene_stim


def test_graph_state_conversion_two_bell_pairs() -> None:
    """
    Test that the graph state conversion works for two Bell pairs.
    """
    tableau = pauli.SignTerms(4)
    tableau.append(pauli.SignTerm(4, {0: pauli.X, 2: pauli.X}))
    tableau.append(pauli.SignTerm(4, {0: pauli.Z, 2: pauli.Z}))
    tableau.append(pauli.SignTerm(4, {1: pauli.X, 3: pauli.X}))
    tableau.append(pauli.SignTerm(4, {1: pauli.Z, 3: pauli.Z}))

    sq_cliffords = convert_to_graph_state(tableau)

    assert sq_cliffords == [SQClifford.I, SQClifford.I, SQClifford.H, SQClifford.H]
    assert str(tableau) == "(+1, X0 Z2), (+1, X1 Z3), (+1, Z0 X2), (+1, Z1 X3)"


@pytest.mark.parametrize("seed", [42, 123, 456, 1234, 999])
def test_arbitrary_stabilizer_state_generation(seed: int) -> None:
    """
    Generate an arbitrary stabilizer state and generate a guppy function that
    prepares it. Then, check that the tableaus match.
    """

    n_qubits = 20

    # Generate a random Clifford circuit in Guppy
    @guppy
    @no_type_check
    def random_clifford_circuit() -> None:
        rng = RNG(comptime(seed))

        qs = array(qubit() for _ in range(comptime(n_qubits)))

        for _ in range(comptime(n_qubits)):  # As many layers as qubits
            for i in range(comptime(n_qubits)):
                pauli_gate = rng.random_int_bounded(4)
                if pauli_gate == 1:
                    x(qs[i])
                elif pauli_gate == 2:
                    y(qs[i])
                elif pauli_gate == 3:
                    z(qs[i])

                clifford_gate = rng.random_int_bounded(4)
                if clifford_gate == 1:
                    s(qs[i])
                if clifford_gate == 2:
                    sdg(qs[i])
                if clifford_gate == 3:
                    h(qs[i])

                target_qubit = rng.random_int_bounded(comptime(n_qubits))
                if target_qubit != i:
                    cx(qs[i], qs[target_qubit])

        rng.discard()

        state_output("original", qs)
        discard_array(qs)

    # Extract the stabilizer tableau
    states_dict = _invoke_selene_stim(random_clifford_circuit, n_qubits)
    stab_list = states_dict["original"].get_reduced_stabilizers()
    original_tableau = stabilizerlist_to_signterms(stab_list)

    # Generate a Guppy function that prepares the same stabilizer state
    prep_func = gen_guppy_state_prep(original_tableau)

    @guppy
    @no_type_check
    def automated_preparation() -> None:
        qs = prep_func()
        state_output("automated", qs)
        discard_array(qs)

    # Extract the stabilizer tableau
    states_dict = _invoke_selene_stim(automated_preparation, n_qubits)
    stab_list = states_dict["automated"].get_reduced_stabilizers()
    automated_tableau = stabilizerlist_to_signterms(stab_list)

    # Check they agree
    original_tableau.canonicalize_all()
    automated_tableau.canonicalize_all()
    assert original_tableau == automated_tableau
