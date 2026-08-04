from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.array import array
from guppylang.std.builtins import comptime
from guppylang.std.debug import state_output
from guppylang.std.quantum import discard_array, qubit
from selene_sim.backends import Stim
from selene_sim.build import build
from selene_stim_plugin import SeleneStimState
from zixy.qubit import pauli

from guppyft.verifier.code import StabilizerCode, identity_code
from guppyft.verifier.expansion import get_expanded_stabilizer_set
from guppyft.verifier.state_gen import gen_choi_state
from guppyft.verifier.utils import (
    DoubleBlockUnitary,
    SingleBlockUnitary,
    stabilizerlist_to_signterms,
)

N = guppy.nat_var("N")


def _invoke_selene_stim(
    main_function: GuppyFunctionDefinition[[], None],
    n_func_qubits: int,
    seed: int = 123,
) -> dict[str, SeleneStimState]:
    instance = build(main_function.compile())
    seeded_stim_instance = Stim(random_seed=seed)
    output = instance.run(simulator=seeded_stim_instance, n_qubits=2 * n_func_qubits)
    return seeded_stim_instance.extract_states_dict(output)


def compute_stabilizers_single_block(
    code: StabilizerCode,
    clifford_func: SingleBlockUnitary,
    n_func_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation.

    :param code: The stabilizer code.
    :param clifford_func: A Guppy function which implements a Clifford unitary
        on a single code block.
    :param n_func_qubits: An upper bound for the number of qubits used in stabilizer
        simulation.
    :return: A Zixy SignTerms instance storing the stabilizers of the Choi state.
    """

    choi_prep = gen_choi_state(code, clifford_func, 1)
    n = code.num_physical_qubits

    @guppy
    def main() -> None:
        controls, targets = choi_prep[comptime(n)]()

        state_output("control", controls)
        state_output("target", targets)
        state_output("total", targets)

        discard_array(controls)
        discard_array(targets)

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(main, n_func_qubits)

    # This is a hack so that we can get a state_output over both the
    #  control and target registers. Currently state result doesn't support passing
    #  more than a single array. The alternative would be doing array concatenation
    #  in Guppy. This seemed easier.
    total = states_dict["total"]
    control_qubits = states_dict["control"].specified_qubits
    target_qubits = states_dict["target"].specified_qubits
    total.specified_qubits = control_qubits + target_qubits
    ########

    stab_list = states_dict["total"].get_reduced_stabilizers()
    return stabilizerlist_to_signterms(stab_list)


def compute_stabilizers_double_block(
    code: StabilizerCode,
    clifford_func: DoubleBlockUnitary,
    n_func_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation across
      two code blocks.

    :param code: The stabilizer code.
    :param clifford_func: A Guppy function which implements a Clifford unitary
      across two code blocks.
    :param n_func_qubits: An upper bound for the number of qubits used in stabilizer
    simulation.
    :return: A Zixy SignTerms instance storing the stabilizers of the Choi state.
    """

    choi_prep = gen_choi_state(code, clifford_func, 2)  # type: ignore[arg-type]
    n = code.num_physical_qubits

    @guppy
    def main() -> None:
        first_controls, first_targets, second_controls, second_targets = choi_prep[
            comptime(n)
        ]()

        state_output("controls1", first_controls)
        state_output("targets1", first_targets)
        state_output("total", first_targets)

        state_output("controls2", second_controls)
        state_output("targets2", second_targets)

        discard_array(first_controls)
        discard_array(first_targets)

        discard_array(second_controls)
        discard_array(second_targets)

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(main, n_func_qubits)

    # Using a hack to get the state_output across four code blocks. See the
    # comment in compute_stabilizers_single_block for more info.
    total = states_dict["total"]
    control_qubits1 = states_dict["controls1"].specified_qubits
    target_qubits1 = states_dict["targets1"].specified_qubits
    control_qubits2 = states_dict["controls2"].specified_qubits
    target_qubits2 = states_dict["targets2"].specified_qubits
    total.specified_qubits = (
        control_qubits1 + target_qubits1 + control_qubits2 + target_qubits2
    )
    ########

    stab_list = states_dict["total"].get_reduced_stabilizers()

    return stabilizerlist_to_signterms(stab_list)


N_PHYSICAL = guppy.nat_var("N_PHYSICAL")
K_LOGICAL = guppy.nat_var("K_LOGICAL")

type SemanticCliffordUnitary = GuppyFunctionDefinition[
    [array[qubit, K_LOGICAL]], None  # type: ignore[valid-type]
]
type ImplementationCliffordUnitary = GuppyFunctionDefinition[
    [array[qubit, N_PHYSICAL]], None  # type: ignore[valid-type]
]


type SemanticCliffordUnitaryDouble = GuppyFunctionDefinition[
    [array[qubit, K_LOGICAL], array[qubit, K_LOGICAL]], None  # type: ignore[valid-type]
]
type ImplementationCliffordUnitaryDouble = GuppyFunctionDefinition[
    [array[qubit, N_PHYSICAL], array[qubit, N_PHYSICAL]], None  # type: ignore[valid-type]
]


def compute_verification_signterms(
    semantic_function: SemanticCliffordUnitary,
    impl_function: ImplementationCliffordUnitary,
    code_definition: StabilizerCode,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Given a semantic Guppy function acting on k qubits and an impl Guppy function
      acting on n qubits, compute a pair of Clifford tableaux. If the implementation
        of the semantic function is valid, the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 2k stabilizers for the 2k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_single_block(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        code_definition.num_logical_qubits,
    )

    # Expand the 2k logical stabilizers to 2k stabilizers of size 2n.
    # We also add the 2(n-k) stabilizer generators of our code.
    # For each code block there are (n-k) so 2 blocks give us 2(n-k).
    # We have 2k + 2(n-k) = 2n stabilizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=1
    )

    # Calculate the 2n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_single_block(
        code_definition,
        impl_function,
        code_definition.num_physical_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_verification_signterms_double_block(
    semantic_function: SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitaryDouble,
    code_definition: StabilizerCode,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Given a semantic Guppy function acting between two code blocks and an
      impl Guppy function acting on n qubits compute a pair of Clifford tableaux.
        If the implementation of the semantic function is valid,
          the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on two code blocks.
    :param impl_function: A Guppy function for implementing
      the semantics on two code blocks.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 4k stabilizers for the 4k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_double_block(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        2 * code_definition.num_logical_qubits,
    )

    # Expand the 4k logical stabilizers and combine them with the generators for each
    #  block. We obtain 4k + 4(n-k) = 4n stablizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=2
    )

    # Calculate the 4n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_double_block(
        code_definition,
        impl_function,
        2 * code_definition.num_physical_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers
