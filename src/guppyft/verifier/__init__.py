"""Functions to verify correctness of logical Clifford gadgets with tableaux comparison.

.. currentmodule:: guppyft.verifier

Supported features
==================

Verifying Cliffords with :py:func:`valid_clifford_implementation`


* Works for :math:`k>1` codes
* Works for operations on a single code block or between two code blocks
* Works for non-CSS codes (e.g. the :math:`[[5, 1, 3]]` code)
* Ancilla qubits can be used in the implementation

The same features are available for :py:func:`valid_pauli_eigenstate_preparation`.

Steane code example
===================

.. code-block:: python

    from guppylang import guppy
    from guppylang.std.builtins import array
    from guppylang.std.quantum import qubit, h

    from guppyft.code_def import StabilizerCode
    from guppyft.verifier import valid_clifford_implementation

    STEANE_DEF = StabilizerCode.from_python_strings(
        num_physical_qubits=7,
        num_logical_qubits=1,
        distance=3,
        generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
        x_logicals=["XXXXXXX"],
        z_logicals=["ZZZZZZZ"],
    )


    @guppy
    def steane_specify_h(qs: array[qubit, 1]) -> None:
        h(qs[0])

    @guppy
    def steane_impl_h(block: array[qubit, 7]) -> None:
        for i in range(len(block)):
            h(block[i])

    # True => implementation is valid
    assert valid_clifford_implementation(steane_specify_h, steane_impl_h, STEANE_DEF)
"""

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
