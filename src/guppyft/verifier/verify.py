from collections.abc import Callable
from typing import TYPE_CHECKING, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.array import array
from guppylang.std.debug import state_result
from guppylang.std.quantum import cx, discard_array, h, qubit
from selene_sim import Stim
from selene_sim.build import build

if TYPE_CHECKING:
    from selene_stim_plugin.state import StabilizerList

from zixy.qubit import Qubits, pauli

from guppyft.verifier.code import StabilizerCode
from guppyft.verifier.gauss import canonicalize
from guppyft.verifier.utils import (
    stabilizerlist_to_signterms,
)

N = guppy.nat_var("N")


SingleBlockUnitary = GuppyFunctionDefinition[[array[qubit, N]], None]
DoubleBlockUnitary = GuppyFunctionDefinition[
    [tuple[array[qubit, N]], array[qubit, N]], None
]


SingleBlockChoiStateFuntion = Callable[
    [SingleBlockUnitary], tuple[array[qubit, N], array[qubit, N]]
]


DoubleBlockChoiStateFuntion = Callable[
    [DoubleBlockUnitary],
    tuple[array[qubit, N], array[qubit, N], array[qubit, N], array[qubit, N]],
]


@guppy
@no_type_check
def default_choi_state_preparation(
    unitary_func: Callable[[array[qubit, N]], None],
) -> tuple[array[qubit, N], array[qubit, N]]:
    control_block = array(qubit() for _ in range(N))
    target_block = array(qubit() for _ in range(N))
    for i in range(N):
        h(control_block[i])
        cx(control_block[i], target_block[i])

    unitary_func(target_block)
    return control_block, target_block


@guppy
@no_type_check
def default_choi_state_preparation_double_block(
    unitary_func: Callable[[array[qubit, N], array[qubit, N]], None],
) -> tuple[array[qubit, N], array[qubit, N], array[qubit, N], array[qubit, N]]:
    first_control_block = array(qubit() for _ in range(N))
    first_target_block = array(qubit() for _ in range(N))
    second_control_block = array(qubit() for _ in range(N))
    second_target_block = array(qubit() for _ in range(N))

    for i in range(N):
        h(first_control_block[i])
        h(second_control_block[i])
        cx(first_control_block[i], first_target_block[i])
        cx(second_control_block[i], second_target_block[i])

    unitary_func(first_target_block, second_target_block)
    return (
        first_control_block,
        first_target_block,
        second_control_block,
        second_target_block,
    )


def compute_stabilizers_single_block(
    clifford_func: SingleBlockUnitary,
    choi_state_preparation: SingleBlockChoiStateFuntion,
    n_func_qubits: int,
    seed: int = 123,
) -> pauli.SignTerms:
    @guppy
    def main() -> None:
        controls, targets = choi_state_preparation(clifford_func)

        state_result("control", controls)
        state_result("target", targets)
        state_result("total", targets)

        discard_array(controls)
        discard_array(targets)

    instance = build(main.compile())
    seeded_stim_instance = Stim(random_seed=seed)
    output = instance.run(simulator=seeded_stim_instance, n_qubits=2 * n_func_qubits)
    states_dict = seeded_stim_instance.extract_states_dict(output)

    # This is a hack so that we can get a state_result over both the control and target registers.
    # Currently state result doesn't support passing more than a single array. The alternative would
    # be doing array concatenation in Guppy. This seemed easier.
    total = states_dict["total"]
    control_qubits = states_dict["control"].specified_qubits
    target_qubits = states_dict["target"].specified_qubits
    total.specified_qubits = control_qubits + target_qubits
    ########

    stab_list: StabilizerList = states_dict["total"].get_reduced_stabilizers()
    return stabilizerlist_to_signterms(stab_list)


def compute_stabilizers_double_block(
    clifford_func: DoubleBlockUnitary,
    choi_state_preparation_double_block: DoubleBlockChoiStateFuntion,
    n_func_qubits: int,
    seed: int = 123,
) -> pauli.SignTerms:
    @guppy
    def main() -> None:
        first_controls, first_targets, second_controls, second_targets = (
            choi_state_preparation_double_block(clifford_func)
        )

        state_result("controls1", first_controls)
        state_result("targets1", first_targets)
        state_result("total", first_targets)

        state_result("controls2", second_controls)
        state_result("targets2", second_targets)

        discard_array(first_controls)
        discard_array(first_targets)

        discard_array(second_controls)
        discard_array(second_targets)

    instance = build(main.compile())
    seeded_stim_instance = Stim(random_seed=seed)
    output = instance.run(simulator=seeded_stim_instance, n_qubits=2 * n_func_qubits)
    states_dict = seeded_stim_instance.extract_states_dict(output)

    # Using a hack to get the state_result across four code blocks. See the
    # comment for compute_stabilizers_single_block for more info.
    total = states_dict["total"]
    control_qubits1 = states_dict["controls1"].specified_qubits
    target_qubits1 = states_dict["targets1"].specified_qubits
    control_qubits2 = states_dict["controls2"].specified_qubits
    target_qubits2 = states_dict["targets2"].specified_qubits
    total.specified_qubits = (
        control_qubits1 + target_qubits1 + control_qubits2 + target_qubits2
    )
    ########

    stab_list: StabilizerList = states_dict["total"].get_reduced_stabilizers()

    return stabilizerlist_to_signterms(stab_list)


# TODO: refactor this function to made smarter use of zixy's implicit padding.
# Using shift_pauli should help.
# Also allow >2 codeblocks.
def pad_code_stabilizers(code: StabilizerCode, num_blocks: int) -> pauli.StringSet:
    code_generators: pauli.StringSet = code.generators
    generator_tuples = code_generators.to_strings().get_tuples()
    padding = tuple([pauli.PauliMatrix.I for _ in range(code.num_physical_qubits)])
    p0_padding = [g + padding for g in generator_tuples]
    if num_blocks == 1:
        p1_padding = [padding + g for g in generator_tuples]
        combined = tuple(p0_padding + p1_padding)
    elif num_blocks == 2:
        p1_padding = [padding + g + 2 * padding for g in generator_tuples]
        p2_padding = [padding * 2 + g + padding for g in generator_tuples]
        p3_padding = [padding * 3 + g for g in generator_tuples]
        combined = tuple(p0_padding + p1_padding + p2_padding + p3_padding)
    else:
        raise ValueError(
            f"Currently no more than two codeblocks are supported. Got argument num_blocks={num_blocks}."
        )

    return pauli.StringSet.from_iterable(
        combined, 2 * num_blocks * code.num_physical_qubits
    )


def shift_pauli(pauli_op: pauli.String, offset: int, size: int) -> pauli.String:
    """
    Shift qubit indices of a String by offset.
    """
    pauli_dict = pauli_op.get_dict()
    original_keys = list(pauli_dict.keys())
    new_keys = [i + offset for i in original_keys]
    new_pauli_dict = dict(zip(new_keys, pauli_dict.values(), strict=True))
    return pauli.String(size, new_pauli_dict)


def expand_pauli_term(
    logical_term: pauli.SignTerm,
    code: StabilizerCode,
    num_blocks: int,
) -> pauli.SignTerm:

    n = code.num_physical_qubits
    k = code.num_logical_qubits
    total_qubit_number = num_blocks * n

    # "result_string" is a Pauli String which will store a single physical Pauli term
    # possibly across multiple code blocks. This String will be one term in the expanded tableau.
    result_string = pauli.String(qubits=total_qubit_number)

    for logical_qubit_index, logical_pauli in logical_term.string.get_dict().items():
        # "non_identity_pauli_index" is the index we need to access to expand the logical operators for a StabilizerCode.
        # Consider StabilizerCode.x_logicals for the Iceberg code.
        # 1. (XI -> XXII) non_identity_pauli_index=0, ICEBERG_4_2_2.x_logicals[0] = XXII
        # 2. (IX -> XIXI) non_identity_pauli_index=1, ICEBERG_4_2_2.x_logicals[1] = XIXI
        non_identity_pauli_index = logical_qubit_index % k

        # logical_block_number tells us which logical code block a specific (logical_qubit, logical_pauli)
        # pair belongs to. If we had 4 logical qubits (q0, q1, q2, q3) from two logical iceberg code blocks then
        # (q0, q1) would correspond to logical_block_number=0 and (q2, q3) would correspond to logical_block_number=1.
        logical_block_number = logical_qubit_index // k

        # For each logical_pauli (PauliMatrix) term in logical_term we get the corresponding physical Pauli
        # by indexing into StabilizerCode.x_logicals/StabilizerCode.z_logicals using the
        # "non_identity_pauli_index" index computed above.
        match logical_pauli:
            case pauli.PauliMatrix.X:
                physical_pauli: pauli.String = code.x_logicals[non_identity_pauli_index]

            case pauli.PauliMatrix.Z:
                physical_pauli: pauli.String = code.z_logicals[non_identity_pauli_index]

            case pauli.PauliMatrix.Y:
                physical_pauli: pauli.String = (
                    code.x_logicals[non_identity_pauli_index]
                    * code.z_logicals[non_identity_pauli_index]
                ).string

            case _:
                raise ValueError(
                    f"Can only expand X, Y and Z Paulis, got {logical_pauli}."
                )

        # "offset" tells us how we need to adjust the qubit indices of physical_pauli
        # depending on which code block we are in. Suppose we had two Steane blocks
        # with seven physical qubits each. If we expanded a logical Pauli in the second logical block
        # Then the appropriate "offset" would be (1*7) = 7.
        offset = logical_block_number * n
        shifted = shift_pauli(physical_pauli, offset, size=total_qubit_number)

        # Obtain the expanded physical Pauli by taking the product of k expanded Strings.
        result_string *= shifted

    return pauli.SignTerm.from_cmpnt_coeff(result_string, logical_term.coeff)


def expand_logical_signterms(
    logical_terms: pauli.SignTerms,
    code: StabilizerCode,
) -> pauli.SignTerms:

    k = code.num_logical_qubits
    num_blocks = len(logical_terms.qubits) // k

    expanded_terms = pauli.SignTerms(
        qubits=Qubits.from_count(num_blocks * code.num_physical_qubits)
    )
    # Expand the logical terms one-by-one using the logical operators
    #  of the Stabilizer code.
    for logical_term in logical_terms:
        expanded = expand_pauli_term(
            logical_term,
            code,
            num_blocks,
        )

        expanded_terms.append(expanded)
    return expanded_terms


def get_expanded_stabilizer_set(
    signed_logical_paulis: pauli.SignTerms, code_def: StabilizerCode, num_blocks: int
) -> pauli.SignTerms:

    expanded_logicals: pauli.SignTerms = expand_logical_signterms(
        signed_logical_paulis, code_def
    )

    sign_terms = pauli.SignTerms.from_str(str(expanded_logicals))

    padded_stabilizers: pauli.StringSet = pad_code_stabilizers(code_def, num_blocks)

    for s in padded_stabilizers.to_strings():
        sign_terms.append(s)
    return sign_terms


N_PHYSICAL = guppy.nat_var("N_PHYSICAL")
K_LOGICAL = guppy.nat_var("K_LOGICAL")

SemanticCliffordUnitary = GuppyFunctionDefinition[[array[qubit, K_LOGICAL]], None]
ImplementationCliffordUnitary = GuppyFunctionDefinition[
    [array[qubit, N_PHYSICAL]], None
]


SemanticCliffordUnitaryDouble = GuppyFunctionDefinition[
    [array[qubit, K_LOGICAL], array[qubit, K_LOGICAL]], None
]
ImplementationCliffordUnitaryDouble = GuppyFunctionDefinition[
    [array[qubit, N_PHYSICAL], array[qubit, N_PHYSICAL]], None
]


def compute_verification_signterms(
    semantic_function: SemanticCliffordUnitary,
    impl_function: ImplementationCliffordUnitary,
    code_choi_state_function: SingleBlockChoiStateFuntion,
    code_definition: StabilizerCode,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:

    # Get the 2k stabilizers for the 2k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_single_block(
        semantic_function,
        choi_state_preparation=default_choi_state_preparation,
        n_func_qubits=code_definition.num_logical_qubits,
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
        impl_function,
        code_choi_state_function,
        code_definition.num_physical_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    canonicalize(expanded_semantic_stabilizers)
    canonicalize(implementation_stabilizers)

    return expanded_semantic_stabilizers, implementation_stabilizers


def compute_verification_signterms_double_block(
    semantic_function: SemanticCliffordUnitaryDouble,
    impl_function: ImplementationCliffordUnitaryDouble,
    code_choi_state_function: DoubleBlockChoiStateFuntion,
    code_definition: StabilizerCode,
) -> tuple[pauli.SignTerms, pauli.SignTerms]:

    # Get the 4k stabilizers for the 4k qubit Choi state encoding the logical operation.
    semantic_choi_stabilizers = compute_stabilizers_double_block(
        clifford_func=semantic_function,
        choi_state_preparation_double_block=default_choi_state_preparation_double_block,
        n_func_qubits=2 * code_definition.num_logical_qubits,
    )

    # Expand the 4k logical stabilizers and combine them with the generators for each block.
    # We obtain 4k + 4(n-k) = 4n stablizers in total.
    expanded_semantic_stabilizers = get_expanded_stabilizer_set(
        semantic_choi_stabilizers, code_definition, num_blocks=2
    )

    # Calculate the 4n stabilizers of the Choi state encoding the physical operation.
    implementation_stabilizers = compute_stabilizers_double_block(
        impl_function,
        code_choi_state_function,
        2 * code_definition.num_physical_qubits,
    )

    # Canonicalize both Clifford Tableaux so that we can test for equality.
    canonicalize(expanded_semantic_stabilizers)
    canonicalize(implementation_stabilizers)

    return expanded_semantic_stabilizers, implementation_stabilizers
