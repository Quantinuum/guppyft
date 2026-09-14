"""Verify logical Clifford gadgets by comparing tableaux.

The verification functions support:

* Codes with more than one logical qubit.
* Operations on one or two code blocks.
* Non-CSS codes, such as the `[[5, 1, 3]]` code.
* Implementations that use ancilla qubits.

The same capabilities are available in `valid_clifford_implementation` and
`valid_stabilizer_state_preparation`.

Examples:
    Verify a Steane-code Hadamard implementation:

        from guppylang import guppy
        from guppylang.std.builtins import array
        from guppylang.std.quantum import h, qubit

        from guppyft.code_def import StabilizerCode
        from guppyft.verify import valid_clifford_implementation

        STEANE_DEF = StabilizerCode.from_python_strings(
            num_physical_qubits=7,
            num_logical_qubits=1,
            distance=3,
            generators=[
                "XXXXIII",
                "IXXIXXI",
                "IIXXIXX",
                "ZZZZIII",
                "IZZIZZI",
                "IIZZIZZ",
            ],
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

        assert valid_clifford_implementation(
            steane_specify_h, steane_impl_h, STEANE_DEF
        )
"""

from ._verify import (
    valid_clifford_implementation,
    valid_stabilizer_state_preparation,
)

__all__ = [
    "valid_clifford_implementation",
    "valid_stabilizer_state_preparation",
]
