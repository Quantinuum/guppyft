from zixy.qubit import Qubits, pauli

from guppyft.code_def import StabilizerCode


def pad_code_stabilizers(code: StabilizerCode, num_blocks: int) -> pauli.SignTermSet:
    """Returns a set of Stabilizers for each of the m codeblocks padded by
      the identity.

    For example, if we have two blocks of the steane code we have
    (n-k) Pauli strings indexed from 0-6 with the identity on qubits 7-13 and
    (n-k) Pauli strings indexed from 7-13 with the identity on qubits 0-6.
    We get a set of pauli strings of size m(n-k).

    Note: Remember that when using Choi states (for unitary testing via map-duality),
      a factor of 2 is needed in the number of codeblocks.

    :param code: A StabilizerCode.
    :param num_blocks: The number of code blocks.
    :return: A set of Pauli strings made up of padded stabilizers
      for each code block. Returns Pauli Strings for m blocks.
    """
    n = code.num_physical_qubits

    combined = []
    for i in range(num_blocks):
        combined += [
            shift_pauli(g, offset=i * n, size=num_blocks * n)  # type: ignore[arg-type]
            for g in code.generators
        ]

    return pauli.SignTermSet.from_iterable(
        combined, num_blocks * code.num_physical_qubits
    )


def shift_pauli(pauli_op: pauli.SignTerm, offset: int, size: int) -> pauli.SignTerm:
    """
    Shift qubit indices of a String (to the right) by an offset.
    """
    pauli_dict = pauli_op.string.get_dict()
    original_keys = list(pauli_dict.keys())
    new_keys = [i + offset for i in original_keys]
    new_pauli_dict = dict(zip(new_keys, pauli_dict.values(), strict=True))
    shifted: pauli.SignTerm = pauli_op.coeff * pauli.String(size, new_pauli_dict)
    return shifted


def expand_pauli_term(
    logical_term: pauli.SignTerm,
    code: StabilizerCode,
    num_blocks: int,
) -> pauli.SignTerm:
    """Expand a single logical Pauli term defined over multiple code blocks using
      the definition of the logical operators for a particular StabilizerCode.

    :param logical_term: The (signed) Pauli term to expand.
    :param code: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_blocks: The number of code blocks represented in the SignTerm.
    :return: An expanded SignTerm which represents the physical implementation
      of the logical term.
    """

    n = code.num_physical_qubits
    k = code.num_logical_qubits
    total_qubit_number = num_blocks * n

    # "result_term" is a Pauli String which will store a single physical Pauli term
    # possibly across multiple code blocks.
    #  This will be one term in the expanded tableau.
    result_term = pauli.SignTerm(qubits=total_qubit_number)

    for logical_qubit_index, logical_pauli in logical_term.string.get_dict().items():
        # "non_identity_pauli_index" is the index we need to access to expand the
        #  logical operators for a StabilizerCode.
        # Consider StabilizerCode.x_logicals for the Iceberg code.
        # 1. (XI -> XXII) non_identity_pauli_index=0, ICEBERG_DEF.x_logicals[0] = XXII
        # 2. (IX -> XIXI) non_identity_pauli_index=1, ICEBERG_DEF.x_logicals[1] = XIXI
        non_identity_pauli_index = logical_qubit_index % k

        # logical_block_number tells us which logical code block a specific
        #  (logical_qubit, logical_pauli) pair belongs to. If we had 4 logical qubit
        #  (q0, q1, q2, q3) from two logical iceberg code blocks then (q0, q1) would
        #  correspond to logical_block_number=0 and (q2, q3) would correspond
        #  to logical_block_number=1.
        logical_block_number = logical_qubit_index // k

        # For each logical_pauli (PauliMatrix) term in logical_term we get the
        #  corresponding physical Pauli by indexing into
        # StabilizerCode.x_logicals/StabilizerCode.z_logicals using the
        # "non_identity_pauli_index" index computed above.
        match logical_pauli:
            case pauli.PauliMatrix.X:
                physical_pauli = code.x_logicals[non_identity_pauli_index]

            case pauli.PauliMatrix.Y:
                physical_pauli = code.y_logicals[non_identity_pauli_index]

            case pauli.PauliMatrix.Z:
                physical_pauli = code.z_logicals[non_identity_pauli_index]

            case _:
                raise ValueError(
                    f"Can only expand X, Y and Z Paulis, got {logical_pauli}."
                )

        # "offset" tells us how we need to adjust the qubit indices of physical_pauli
        # depending on which code block we are in. Suppose we had two Steane blocks
        # with seven physical qubits each. If we expanded a logical Pauli in the second
        #  logical block, then the appropriate "offset" would be (1*7) = 7.
        offset = logical_block_number * n

        shifted = shift_pauli(physical_pauli, offset, size=total_qubit_number)  # type: ignore[arg-type]

        # Get final expanded term by taking the product of num_blocks*k expanded terms.
        result_term *= shifted

    result_term *= logical_term.coeff
    assert isinstance(result_term, pauli.SignTerm)
    return result_term


def expand_logical_signterms(
    logical_terms: pauli.SignTerms,
    code: StabilizerCode,
) -> pauli.SignTerms:
    """Given a tableau made up of signed Pauli terms, expand each term according
      as prescribed by the logical operators of a StabilizerCode.

    :param logical_terms: A tableau of signed Pauli terms to be expanded.
    :param code: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :return: An expanded SignTerms tableau.
    """
    k = code.num_logical_qubits
    num_blocks = len(logical_terms.qubits) // k

    expanded_terms = pauli.SignTerms(
        qubits=Qubits.from_count(num_blocks * code.num_physical_qubits)
    )
    # Expand the logical terms one-by-one using the logical operators
    #  of the Stabilizer code.
    for logical_term in logical_terms:
        assert isinstance(logical_term, pauli.SignTerm)
        expanded = expand_pauli_term(
            logical_term,
            code,
            num_blocks,
        )

        expanded_terms.append(expanded)
    return expanded_terms


def get_expanded_stabilizer_set(
    signed_logical_paulis: pauli.SignTerms, code: StabilizerCode, num_blocks: int
) -> pauli.SignTerms:
    """Given a tableau of signed logical Pauli terms and a number of codeblocks(m),
      expand the terms according to the logical operators of a StabilizerCode.
        These expanded Paulis are also combined with the padded
          Stabilizer generators to give mn terms in total.

    :param signed_logical_paulis: A tableau of signed Pauli terms to be expanded.
    :param code: A stabilizer code with well defined [[n, k, d]] parameters
      and logical operators.
    :param num_blocks: The number of code blocks represented in signed_logical_paulis.
    :return: An expanded SignTerms tableau.
    """

    # Firstly, we expand the stabilizers of the state using the
    # logical operators of the StabilizerCode
    stabilizers: pauli.SignTerms = expand_logical_signterms(signed_logical_paulis, code)
    # Secondly, we include the stabilizer generators for each code block.
    padded_stabilizers: pauli.SignTermSet = pad_code_stabilizers(code, num_blocks)

    for s in padded_stabilizers:
        stabilizers.append(s)
    return stabilizers
