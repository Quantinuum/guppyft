from typing import no_type_check

from selene_stim_plugin.state import Stabilizer, StabilizerList
from zixy.qubit import pauli

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit, measure_array, collect_measurements

from guppyft.verifier.utils import (
    selene_stabilizer_to_zixy_signterm,
    stabilizerlist_to_signterms,
    array_slicer,
)


def test_selene_to_zixy() -> None:
    stab = Stabilizer("-XZXXY")
    converted_op = selene_stabilizer_to_zixy_signterm(stab)
    assert isinstance(converted_op, pauli.SignTerm)
    assert str(converted_op) == "(-1, X0 Z1 X2 X3 Y4)"


def test_stabilizer_list_to_stringset() -> None:
    stab_list = StabilizerList(["-XZXXY", "+XZZZY", "-ZXXXY"])
    signterms = stabilizerlist_to_signterms(stab_list)
    assert isinstance(signterms, pauli.SignTerms)
    assert (
        str(signterms)
        == "(-1, X0 Z1 X2 X3 Y4), (+1, X0 Z1 Z2 Z3 Y4), (-1, Z0 X1 X2 X3 Y4)"
    )


def test_partition_array_int() -> None:
    @guppy
    @no_type_check
    def main() -> None:
        arr = array(1, 2, 3, 4, 5, 6, 7)
        slicer = array_slicer(arr)

        slice0 = slicer.take(2)
        slice1 = slicer.take(3)
        slice2 = slicer.take(2)

        if slice0[0] == 1 and slice0[1] == 2:
            result("success", 0)
        if slice1[0] == 3 and slice1[1] == 4 and slice1[2] == 5:
            result("success", 1)
        if slice2[0] == 6 and slice2[1] == 7:
            result("success", 2)

    dict_results = main.emulator(n_qubits=1).run().collated_shots()
    assert dict_results[0]["success"] == [0, 1, 2]


def test_partition_array_qubit() -> None:
    @guppy
    @no_type_check
    def main() -> None:
        arr = array(qubit() for _ in range(10))
        slicer = array_slicer(arr)

        slice0 = slicer.take(5)
        slice1 = slicer.take(3)
        slice2 = slicer.take(2)

        slicer.discard_empty()

        result("slice0", collect_measurements(measure_array(slice0)))
        result("slice1", collect_measurements(measure_array(slice1)))
        result("slice2", collect_measurements(measure_array(slice2)))

    dict_results = main.emulator(n_qubits=10).run().collated_shots()[0]
    assert dict_results["slice0"] == [[0, 0, 0, 0, 0]]
    assert dict_results["slice1"] == [[0, 0, 0]]
    assert dict_results["slice2"] == [[0, 0]]