from typing import Generic, Self, no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, comptime, owned
from guppylang.std.collections import Queue, empty_queue
from guppylang.std.num import nat
from guppylang.std.quantum import qubit
from selene_stim_plugin.state import Pauli, Phase, Stabilizer, StabilizerList
from zixy.container.coeffs import Sign
from zixy.qubit import pauli

N = guppy.nat_var("N")

type SingleBlockUnitary = GuppyFunctionDefinition[[array[qubit, N]], None]  # type: ignore[valid-type]
type DoubleBlockUnitary = GuppyFunctionDefinition[
    [array[qubit, N], array[qubit, N]], None  # type: ignore[valid-type]
]
type SingleBlockState = GuppyFunctionDefinition[[], array[qubit, N]]  # type: ignore[valid-type]
type DoubleBlockState = GuppyFunctionDefinition[
    [], tuple[array[qubit, N], array[qubit, N]]  # type: ignore[valid-type]
]


def _convert_pauli(selene_pauli: Pauli) -> pauli.PauliMatrix:
    "Convert a selene_stim_plugin.state.Pauli to a zixy.qubit.pauli.PauliMatrix."
    match selene_pauli:
        case selene_pauli.X:
            return pauli.PauliMatrix.X
        case selene_pauli.Y:
            return pauli.PauliMatrix.Y
        case selene_pauli.Z:
            return pauli.PauliMatrix.Z
        case selene_pauli.I:
            return pauli.PauliMatrix.I


def _get_real_phase(selene_phase: Phase) -> Sign:
    "Convert a selene Pauli phase to zixy. Phase must be real valued."
    match selene_phase:
        case Phase.REAL_POSITIVE:
            return Sign(0)
        case Phase.REAL_NEGATIVE:
            return Sign(1)
        case _:
            raise ValueError(
                f"The phase of a SignTerm must be real! Got {selene_phase}"
            )


def selene_stabilizer_to_zixy_signterm(stabilizer: Stabilizer) -> pauli.SignTerm:
    """Convert a selene_stim_plugin.state.Stabilizer to a zixy.qubit.pauli.SignTerm.

    :param stabilizer: A signed pauli Stabilizer in Selene's representation.
    :return: A Zixy SignTerms instance.
    """
    zixy_paulis: tuple[pauli.PauliMatrix, ...] = tuple(
        [_convert_pauli(p) for p in stabilizer.paulis]
    )
    term = pauli.SignTerm(len(zixy_paulis), zixy_paulis)
    signed_phase = _get_real_phase(stabilizer.phase)
    term.coeff = signed_phase
    return term


def stabilizerlist_to_signterms(stab_list: StabilizerList) -> pauli.SignTerms:
    """Convert a list of signed Pauli stablizers to zixy's representation.

    :param stab_list: A list of stabilizer's in Selene's representation.
    :return: a zixy SignTerms instance equivalent to stab_list.
    """
    sign_terms = pauli.SignTerms(qubits=len(stab_list.generators[0].paulis))
    for gen in stab_list.generators:
        term = selene_stabilizer_to_zixy_signterm(gen)
        sign_terms.append(term)
    return sign_terms


N = guppy.nat_var("N")
T = guppy.type_var("T", copyable=False, droppable=False)


@guppy.struct
@no_type_check
class ArraySlicer(Generic[T, N]):  # type: ignore[misc]
    _queue: Queue[T, N]  # type: ignore[type-arg, valid-type]

    @guppy
    @no_type_check
    def discard_empty(self: Self @ owned) -> None:
        self._queue.discard_empty()

    @guppy
    @no_type_check
    def take(self, n: nat @ comptime) -> array[T, "n"]:
        if n > len(self._queue):
            exit("Cannot take more items than are available in the slicer.")
        return array(self._queue.pop() for _ in range(n))


@guppy
@no_type_check
def array_slicer(arr: array[T, N] @ owned) -> ArraySlicer[T, N]:
    queue = empty_queue[T, N]()
    for q in arr:
        queue.push(q)
    return ArraySlicer(queue)
