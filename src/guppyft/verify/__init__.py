"""Functions to verify correctness of logical Clifford gadgets with tableaux comparison.

.. currentmodule:: guppyft.verify

Supported features
==================

Verifying Cliffords with :py:func:`valid_clifford_implementation`


* Works for :math:`k>1` codes
* Works for operations on a single code block or between two code blocks
* Works for non-CSS codes (e.g. the :math:`[[5, 1, 3]]` code)
* Ancilla qubits can be used in the implementation

The same features are available for :py:func:`valid_stabilizer_state_preparation`.

See the :doc:`/examples/clifford_verification` tutorial for more details.
"""

from ._verify import (
    valid_clifford_implementation,
    valid_stabilizer_state_preparation,
)

__all__ = [
    "valid_clifford_implementation",
    "valid_stabilizer_state_preparation",
]
