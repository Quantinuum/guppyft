from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit

from guppyft.code.steane.primitives import prep_zero_non_ft
from guppyft.code_def import StabilizerCode
from guppyft.verifier import compute_verification_signterms_single_block_state

STEANE_DEF = StabilizerCode.from_python_strings(
    num_physical_qubits=7,
    num_logical_qubits=1,
    distance=3,
    generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
    x_logicals=["XXXXXXX"],
    z_logicals=["ZZZZZZZ"],
)


@guppy
@no_type_check
def specify_zero_state() -> array[qubit, 1]:
    return array(qubit())


def test_steane_prep_zero_non_ft() -> None:
    sem, impl = compute_verification_signterms_single_block_state(
        specify_zero_state,
        prep_zero_non_ft,
        code_definition=STEANE_DEF,
    )
    assert sem == impl
