import inspect
from typing import get_origin

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

from guppyft.code_def import StabilizerCode, identity_code
from guppyft.verifier.expansion import get_expanded_stabilizer_set
from guppyft.verifier.state_gen import gen_choi_state
from guppyft.verifier.utils import (
    DoubleBlockState,
    DoubleBlockUnitary,
    SingleBlockState,
    SingleBlockUnitary,
    stabilizerlist_to_signterms,
)


def _invoke_selene_stim(
    main_function: GuppyFunctionDefinition[[], None],
    num_selene_qubits: int,
    seed: int = 123,
) -> dict[str, SeleneStimState]:
    instance = build(main_function.compile())
    seeded_stim_instance = Stim(random_seed=seed)
    output = instance.run(simulator=seeded_stim_instance, n_qubits=num_selene_qubits)
    return seeded_stim_instance.extract_states_dict(output)


def compute_stabilizers_single_block_state(
    state_prep_func: SingleBlockState,
    num_selene_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation.

    :param state_prep_func: A Guppy function which prepares the stabilizer state
        on a single code block.
    :param num_selene_qubits: An upper bound for the number of qubits
          used in state_prep_func.
    :return: A Zixy SignTerms instance storing the stabilizers of the Choi state.
    """

    @guppy
    def main() -> None:
        block = state_prep_func()
        state_output("total", block)
        discard_array(block)

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(
        main, num_selene_qubits
    )

    stab_list = states_dict["total"].get_reduced_stabilizers()
    return stabilizerlist_to_signterms(stab_list)


def compute_stabilizers_double_block_state(
    state_prep_func: DoubleBlockState,
    num_selene_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation.

    :param state_prep_func: A Guppy function which prepares the stabilizer state
        on two code blocks.
    :param num_selene_qubits: An upper bound for the number of qubits
          used in state_prep_func.
    :return: A Zixy SignTerms instance storing the stabilizers of the Choi state.
    """

    @guppy
    def main() -> None:
        block0, block1 = state_prep_func()
        state_output("block0", block0)
        state_output("block1", block1)
        state_output("total", block0)

        discard_array(block0)
        discard_array(block1)

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(
        main, num_selene_qubits
    )

    # This is a hack so that we can get a state_output over both blocks
    total = states_dict["total"]
    b0_qubits = states_dict["block0"].specified_qubits
    b1_qubits = states_dict["block1"].specified_qubits
    total.specified_qubits = b0_qubits + b1_qubits
    ########

    stab_list = states_dict["total"].get_reduced_stabilizers()
    return stabilizerlist_to_signterms(stab_list)


def compute_stabilizers_single_block_unitary(
    code: StabilizerCode,
    clifford_func: SingleBlockUnitary,
    num_selene_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation.

    :param code: The stabilizer code.
    :param clifford_func: A Guppy function which implements a Clifford unitary
        on a single code block.
    :param num_selene_qubits: An upper bound for the number of qubits
      used in the Choi state for clifford_func.
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

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(
        main, num_selene_qubits=num_selene_qubits
    )

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


def compute_stabilizers_double_block_unitary(
    code: StabilizerCode,
    clifford_func: DoubleBlockUnitary,
    num_selene_qubits: int,
) -> pauli.SignTerms:
    """Compute the stabilizers of a Choi state encoding a Clifford operation across
      two code blocks.

    :param code: The stabilizer code.
    :param clifford_func: A Guppy function which implements a Clifford unitary
      across two code blocks.
    :param num_selene_qubits: An upper bound for the number of qubits
      used in the Choi state for clifford_func.
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

    states_dict: dict[str, SeleneStimState] = _invoke_selene_stim(
        main, num_selene_qubits
    )

    # Using a hack to get the state_output across four code blocks. See the
    # comment in compute_stabilizers_single_block_unitary for more info.
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

type SemanticStabilizerState = GuppyFunctionDefinition[
    [], array[qubit, K_LOGICAL]  # type: ignore[valid-type]
]
type ImplementationStabilizerState = GuppyFunctionDefinition[
    [], array[qubit, N_PHYSICAL]  # type: ignore[valid-type]
]


type SemanticStabilizerStateDouble = GuppyFunctionDefinition[
    [], tuple[array[qubit, K_LOGICAL], array[qubit, K_LOGICAL]]  # type: ignore[valid-type]
]
type ImplementationStabilizerStateDouble = GuppyFunctionDefinition[
    [], tuple[array[qubit, N_PHYSICAL], array[qubit, N_PHYSICAL]]  # type: ignore[valid-type]
]


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


def compute_verification_signterms_single_block_state(
    semantic_function: SemanticStabilizerState,
    impl_function: ImplementationStabilizerState,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute tableaux to verify correctness of stabilizer state preparation.

    Given a semantic Guppy function acting on k qubits and an impl Guppy function
      acting on n qubits, compute a pair of stabilizer tableaux. If the implementation
      of the semantic function is valid, the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_ancilla_qubits: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of stabilizer tableaux made up of signed Pauli terms.
    """
    # Get the k stabilizers for the k qubit state.
    semantic_stabilizers = compute_stabilizers_single_block_state(
        semantic_function,
        code_definition.num_logical_qubits + num_ancilla_qubits,
    )

    # Expand the k logical stabilizers to k stabilizers of size n.
    # We also add the (n-k) stabilizer generators of our code.
    # We have k + (n-k) = n stabilizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_stabilizers, code_definition, num_blocks=1
    )

    # Calculate the n stabilizers of the physical state.
    implementation_stabilizers = compute_stabilizers_single_block_state(
        impl_function,
        code_definition.num_physical_qubits + num_ancilla_qubits,
    )

    # Canonicalize both tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers


def check_stabilizer_state_semantics(
    semantic_function: SemanticStabilizerState | SemanticStabilizerStateDouble,
    impl_function: ImplementationStabilizerState | ImplementationStabilizerStateDouble,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> bool:
    # Get the return type of semantic_function.
    sem_return_annotation = inspect.signature(
        semantic_function.wrapped.python_func  # type: ignore[attr-defined]
    ).return_annotation

    # Check if return annotation is a tuple (acts on two code blocks).
    # Determine whether semantic_function is a SemanticStabilizerStateDouble or not.
    if get_origin(sem_return_annotation) is tuple:
        sem, impl = compute_verification_signterms_double_block_state(
            semantic_function,  # type: ignore[arg-type]
            impl_function,  # type: ignore[arg-type]
            code_definition,
            num_ancilla_qubits,
        )
    else:
        # Here our semantic function is a single block state preparation.
        sem, impl = compute_verification_signterms_single_block_state(
            semantic_function,  # type: ignore[arg-type]
            impl_function,  # type: ignore[arg-type]
            code_definition,
            num_ancilla_qubits,
        )

    return sem == impl


def check_clifford_semantics(
    semantic_function: SemanticCliffordUnitary | SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitary | ImplementationCliffordUnitaryDouble,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> bool:
    sem_signature = inspect.signature(semantic_function.wrapped.python_func)  # type: ignore[attr-defined]
    impl_signature = inspect.signature(impl_function.wrapped.python_func)  # type: ignore[attr-defined]
    if len(sem_signature.parameters) != len(impl_signature.parameters):
        raise TypeError(
            "semantic_function and impl_function have incompatible signatures"
        )
    match len(sem_signature.parameters):
        case 1:
            sem, impl = compute_verification_signterms_single_block_unitary(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                num_ancilla_qubits,
            )
        case 2:
            sem, impl = compute_verification_signterms_double_block_unitary(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                num_ancilla_qubits,
            )
        case _:
            raise TypeError(
                "Unsupported number of code block parameters in semantic_function."
                + f"Got {len(sem_signature.parameters)}, only 1 and 2 are supported."
            )

    return sem == impl


def compute_verification_signterms_double_block_state(
    semantic_function: SemanticStabilizerStateDouble,
    impl_function: ImplementationStabilizerStateDouble,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute tableaux to verify 2 block stabilizer state preparation.

    Given a semantic Guppy function acting on 2k qubits and an impl Guppy function
      acting on 2n qubits, compute a pair of stabilizer tableaux. If the implementation
      of the semantic function is valid, the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on 2k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on 2n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_ancilla_qubits: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of stabilizer tableaux made up of signed Pauli terms.
    """
    # Get the 2k stabilizers for the 2k qubit state.
    semantic_stabilizers = compute_stabilizers_double_block_state(
        semantic_function,
        2 * code_definition.num_logical_qubits + num_ancilla_qubits,
    )

    # Expand the 2k logical stabilizers to 2k stabilizers of size 2n.
    # We also add the 2(n-k) stabilizer generators of our code.
    # We have 2k + 2(n-k) = 2n stabilizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_stabilizers, code_definition, num_blocks=2
    )

    # Calculate the 2n stabilizers of the physical state.
    implementation_stabilizers = compute_stabilizers_double_block_state(
        impl_function,
        2 * code_definition.num_physical_qubits + num_ancilla_qubits,
    )

    # Canonicalize both tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_verification_signterms_single_block_unitary(
    semantic_function: SemanticCliffordUnitary,
    impl_function: ImplementationCliffordUnitary,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute tableaux to verify correctness of Clifford unitary implementation.

    Given a semantic Guppy function acting on k qubits and an impl Guppy function
      acting on n qubits, compute a pair of Clifford tableaux. If the implementation
      of the semantic function is valid, the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_ancilla_qubits: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 2k stabilizers for the 2k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_single_block_unitary(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        num_selene_qubits=2 * (code_definition.num_logical_qubits) + num_ancilla_qubits,
    )

    # Expand the 2k logical stabilizers to 2k stabilizers of size 2n.
    # We also add the 2(n-k) stabilizer generators of our code.
    # For each code block there are (n-k) so 2 blocks give us 2(n-k).
    # We have 2k + 2(n-k) = 2n stabilizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=2
    )

    # Calculate the 2n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_single_block_unitary(
        code_definition,
        impl_function,
        num_selene_qubits=2 * (code_definition.num_physical_qubits)
        + num_ancilla_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_verification_signterms_double_block_unitary(
    semantic_function: SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitaryDouble,
    code_definition: StabilizerCode,
    num_ancilla_qubits: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute tableaux to verify correctness of 2 block Clifford unitary.

    Given a semantic Guppy function acting between two code blocks and an
      impl Guppy function acting on n qubits compute a pair of Clifford tableaux.
      If the implementation of the semantic function is valid,
      the two tableaux will be equivalent.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on two code blocks.
    :param impl_function: A Guppy function for implementing
      the semantics on two code blocks.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_ancilla_qubits: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 4k stabilizers for the 4k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_double_block_unitary(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        num_selene_qubits=4 * (code_definition.num_logical_qubits) + num_ancilla_qubits,
    )

    # Expand the 4k logical stabilizers and combine them with the generators for each
    #  block. We obtain 4k + 4(n-k) = 4n stablizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=4
    )

    # Calculate the 4n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_double_block_unitary(
        code_definition,
        impl_function,
        num_selene_qubits=4 * (code_definition.num_physical_qubits)
        + num_ancilla_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    expanded_semantic_stabilizers.canonicalize_all()
    implementation_stabilizers.canonicalize_all()

    return expanded_semantic_stabilizers, implementation_stabilizers
