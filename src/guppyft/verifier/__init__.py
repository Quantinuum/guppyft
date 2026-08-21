"""Tools for verifying the correctness of logical Clifford gadgets."""

from .utils import (
    selene_stabilizer_to_zixy_signterm,
    stabilizerlist_to_signterms,
)
from .verify import (
    compute_stabilizers_double_block_unitary,
    compute_stabilizers_single_block_unitary,
    compute_tableaux_double_block_state,
    compute_tableaux_double_block_unitary,
    compute_tableaux_single_block_state,
    compute_tableaux_single_block_unitary,
    valid_clifford_implementation,
    valid_pauli_eigenstate_preparation,
)

__all__ = [
    "compute_stabilizers_double_block_unitary",
    "compute_stabilizers_single_block_unitary",
    "compute_tableaux_double_block_state",
    "compute_tableaux_double_block_unitary",
    "compute_tableaux_single_block_state",
    "compute_tableaux_single_block_unitary",
    "selene_stabilizer_to_zixy_signterm",
    "stabilizerlist_to_signterms",
    "valid_clifford_implementation",
    "valid_pauli_eigenstate_preparation",
]
