import inspect
from typing import get_args, get_origin

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import comptime
from guppylang.std.debug import state_output
from guppylang.std.quantum import discard_array
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
    ImplementationCliffordUnitary,
    ImplementationCliffordUnitaryDouble,
    ImplementationStabilizerState,
    ImplementationStabilizerStateDouble,
    SemanticCliffordUnitary,
    SemanticCliffordUnitaryDouble,
    SemanticStabilizerState,
    SemanticStabilizerStateDouble,
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


def compute_tableaux_single_block_state(
    semantic_function: SemanticStabilizerState,
    impl_function: ImplementationStabilizerState,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute a tableaux pair for Pauli eigenstate preparation over one code block.

    Given a semantic Guppy function acting on k qubits and an impl Guppy function
    acting on n qubits, compute a pair of stabilizer tableaux. Note that we will need
    to canonicalize with SignTerms.canonicalize_all() before we can check for equality.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of stabilizer tableaux made up of signed Pauli terms.
    """
    # Get the k stabilizers for the k qubit state.
    semantic_stabilizers = compute_stabilizers_single_block_state(
        semantic_function,
        code_definition.num_logical_qubits + impl_num_ancillas,
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
        code_definition.num_physical_qubits + impl_num_ancillas,
    )

    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_tableaux_double_block_state(
    semantic_function: SemanticStabilizerStateDouble,
    impl_function: ImplementationStabilizerStateDouble,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute a tableaux pair for Pauli eigenstate preparation over two code blocks.

    Given a semantic Guppy function acting on 2k qubits and an impl Guppy function
      acting on 2n qubits, compute a pair of stabilizer tableaux. Note that we will need
    to canonicalize with SignTerms.canonicalize_all() before we can check for equality.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on 2k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on 2n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of stabilizer tableaux made up of signed Pauli terms.
    """
    # Get the 2k stabilizers for the 2k qubit state.
    semantic_stabilizers = compute_stabilizers_double_block_state(
        semantic_function,
        2 * code_definition.num_logical_qubits + impl_num_ancillas,
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
        2 * code_definition.num_physical_qubits + impl_num_ancillas,
    )

    return expanded_semantic_stabilizers, implementation_stabilizers


# TODO: can we clean up this nasty signature hacking function?
def _count_blocks_state(
    semantic_function: SemanticStabilizerState | SemanticStabilizerStateDouble,
    impl_function: ImplementationStabilizerState | ImplementationStabilizerStateDouble,
) -> int:
    # Get the return type of semantic_function.
    sem_return_annotation = inspect.signature(
        semantic_function.wrapped.python_func  # type: ignore[attr-defined]
    ).return_annotation

    impl_return_annotation = inspect.signature(
        impl_function.wrapped.python_func  # type: ignore[attr-defined]
    ).return_annotation

    if get_origin(sem_return_annotation) is tuple:
        if get_origin(impl_return_annotation) is not tuple:
            raise TypeError(
                "semantic_function and impl_function have incompatible signatures"
            )
        # Get the size of the tuple used in the return type. Assumes fixed size.
        size = len(get_args(sem_return_annotation))
        if size > 2:
            raise TypeError(
                "semantic_function has an unsupported return type."
                f" Only tuples of length two are supported. Got {size}."
            )
        return 2
    # If the state prep function does not return a tuple, it represents a single block.
    else:
        return 1


def valid_stabilizer_state_preparation(
    semantic_function: SemanticStabilizerState | SemanticStabilizerStateDouble,
    impl_function: ImplementationStabilizerState | ImplementationStabilizerStateDouble,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> bool:
    """Checks whether impl_function prepares the state specified by semantic function.

    Can check implementations logical Pauli eigenstate preparation
      across one or two code blocks.

    :param semantic_function: A Guppy function for semantic action
      of Pauli eigenstate preparation over one or two code blocks.
    :param impl_function: A Guppy function for preparing the logical eigenstate
      over one or two code blocks.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A Boolean indicating whether the state preparation is valid.
    """
    num_blocks = _count_blocks_state(semantic_function, impl_function)
    match num_blocks:
        case 1:
            sem_stabilizers, impl_stabilizers = compute_tableaux_single_block_state(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                impl_num_ancillas,
            )
        case 2:
            sem_stabilizers, impl_stabilizers = compute_tableaux_double_block_state(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                impl_num_ancillas,
            )
        case _:
            raise TypeError(
                "Unsupported number of code block parameters in semantic_function."
                + f"Got {num_blocks} blocks. Only 1 and 2 are supported."
            )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    sem_stabilizers.canonicalize_all()
    impl_stabilizers.canonicalize_all()

    return sem_stabilizers == impl_stabilizers


def compute_tableaux_single_block_unitary(
    semantic_function: SemanticCliffordUnitary,
    impl_function: ImplementationCliffordUnitary,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute a pair of tableaux for a logical Clifford on a single code block.

    Given a semantic Guppy function acting on k qubits and an impl Guppy function
      acting on n qubits, compute a pair of Clifford tableaux. Note that we will need to
    canonicalize with SignTerms.canonicalize_all() before we can check for equality.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on k logical qubits.
    :param impl_function: A Guppy function for implementing
      the semantics on n physical qubits.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 2k stabilizers for the 2k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_single_block_unitary(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        num_selene_qubits=2 * (code_definition.num_logical_qubits) + impl_num_ancillas,
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
        num_selene_qubits=2 * (code_definition.num_physical_qubits) + impl_num_ancillas,
    )
    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_tableaux_double_block_unitary(
    semantic_function: SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitaryDouble,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:
    """Compute a pair of tableaux for a logical Clifford across two code blocks.

    Given a semantic Guppy function acting between two code blocks and an
      impl Guppy function acting on n qubits compute a pair of Clifford tableaux.
    Note that we will need to canonicalize with SignTerms.canonicalize_all() before
      we can check for equality.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on two code blocks.
    :param impl_function: A Guppy function for implementing
      the semantics on two code blocks.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A pair of Clifford tableaux made up of signed Pauli terms.
    """

    # Get the 4k stabilizers for the 4k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_double_block_unitary(
        identity_code(code_definition.num_logical_qubits),
        semantic_function,
        num_selene_qubits=4 * (code_definition.num_logical_qubits) + impl_num_ancillas,
    )

    # Expand the 4k logical stabilizers and combine them with the generators for each
    #  block. We obtain 4k + 4(n-k) = 4n stabilizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=4
    )

    # Calculate the 4n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_double_block_unitary(
        code_definition,
        impl_function,
        num_selene_qubits=4 * (code_definition.num_physical_qubits) + impl_num_ancillas,
    )
    return expanded_semantic_stabilizers, implementation_stabilizers


def _count_blocks_unitary(
    semantic_function: SemanticCliffordUnitary | SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitary | ImplementationCliffordUnitaryDouble,
) -> int:
    sem_signature = inspect.signature(semantic_function.wrapped.python_func)  # type: ignore[attr-defined]
    impl_signature = inspect.signature(impl_function.wrapped.python_func)  # type: ignore[attr-defined]
    if len(sem_signature.parameters) != len(impl_signature.parameters):
        raise TypeError(
            "semantic_function and impl_function have incompatible signatures"
        )
    num_blocks = len(sem_signature.parameters)
    return num_blocks


def valid_clifford_implementation(
    semantic_function: SemanticCliffordUnitary | SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitary | ImplementationCliffordUnitaryDouble,
    code_definition: StabilizerCode,
    impl_num_ancillas: int = 0,
) -> bool:
    """Checks whether impl_function is a valid implementation of semantic_function.

    Can check implementations of Clifford semantics across one or two code blocks.

    :param semantic_function: A Guppy function for semantic action
      of a Clifford operator on one or two code blocks.
    :param impl_function: A Guppy function for implementing
      the semantics on one or two code blocks.
    :param code_definition: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param impl_num_ancillas: The number of ancilla qubits used in the
        implementation. Defaults to zero.
    :return: A Boolean indicating whether the implementation is valid.
    """
    # Check whether input is a SemanticCliffordUnitary or SemanticCliffordUnitaryDouble.
    num_blocks = _count_blocks_unitary(semantic_function, impl_function)
    match num_blocks:
        case 1:
            sem_stabilizers, impl_stabilizers = compute_tableaux_single_block_unitary(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                impl_num_ancillas,
            )
        case 2:
            sem_stabilizers, impl_stabilizers = compute_tableaux_double_block_unitary(
                semantic_function,  # type: ignore[arg-type]
                impl_function,  # type: ignore[arg-type]
                code_definition,
                impl_num_ancillas,
            )
        case _:
            raise TypeError(
                "Unsupported number of code block parameters in semantic_function."
                + f"Got {num_blocks} blocks. Only 1 and 2 are supported."
            )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    sem_stabilizers.canonicalize_all()
    impl_stabilizers.canonicalize_all()

    return sem_stabilizers == impl_stabilizers
