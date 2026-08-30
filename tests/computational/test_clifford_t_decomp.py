from itertools import product

import pytest
from guppylang import comptime, guppy
from guppylang.std.builtins import output
from guppylang.std.quantum import measure, qubit, x

from guppyft.computational.clifford_t_decomp import toffoli


@pytest.mark.parametrize(
    ("ctrl0_value", "ctrl1_value", "target_value"),
    list(product([False, True], repeat=3)),
)
def test_toffoli(ctrl0_value: bool, ctrl1_value: bool, target_value: bool) -> None:
    @guppy
    def main() -> None:
        ctrl0, ctrl1, target = qubit(), qubit(), qubit()
        if comptime(ctrl0_value):
            x(ctrl0)
        if comptime(ctrl1_value):
            x(ctrl1)
        if comptime(target_value):
            x(target)

        toffoli(ctrl0, ctrl1, target)

        output("ctrl0", measure(ctrl0).read())
        output("ctrl1", measure(ctrl1).read())
        output("target", measure(target).read())

    shots = main.emulator(n_qubits=3).run().collated_shots()

    assert shots == [
        {
            "ctrl0": [int(ctrl0_value)],
            "ctrl1": [int(ctrl1_value)],
            "target": [int(target_value ^ (ctrl0_value and ctrl1_value))],
        }
    ]
