from itertools import product

import pytest
from guppylang import comptime, guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.angles import pi
from guppylang.std.builtins import output
from guppylang.std.quantum import h, measure, qubit, rz, toffoli, x

from guppyft.computational.decomposition import (
    RzDecomposer,
    decompose_rz,
    decompose_toffoli,
)


@pytest.mark.parametrize(
    ("ctrl0_value", "ctrl1_value", "target_value"),
    list(product([False, True], repeat=3)),
)
def test_decompose_toffoli(
    ctrl0_value: bool, ctrl1_value: bool, target_value: bool
) -> None:
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

    pkg = main.compile()
    decompose_toffoli().run(pkg.modules[0], inplace=True)

    shots = EmulatorBuilder().build(pkg, n_qubits=3).run().collated_shots()

    assert shots == [
        {
            "ctrl0": [int(ctrl0_value)],
            "ctrl1": [int(ctrl1_value)],
            "target": [int(target_value ^ (ctrl0_value and ctrl1_value))],
        }
    ]


@pytest.mark.parametrize(
    "method",
    [
        pytest.param(
            RzDecomposer.GRIDSYNTH,
            marks=pytest.mark.xfail(reason="Not currently supported"),
        ),
        RzDecomposer.COMPARATOR_BASED,
    ],
)
def test_decompose_rz(method: RzDecomposer) -> None:
    epsilon = 0.01
    n_ancillas = method.num_ancilla(epsilon)

    @guppy
    def main() -> None:
        q = qubit()
        h(q)
        # Apply a total of rz(pi)
        rz(q, pi / 12)
        rz(q, 5 * pi / 6)
        rz(q, pi / 12)
        h(q)
        output("q", measure(q).read())

    pkg = main.with_minimal_opt().compile()
    decompose_rz(method, epsilon).run(pkg.modules[0], inplace=True)

    shots = (
        EmulatorBuilder()
        .build(pkg, n_qubits=1 + n_ancillas)
        .with_shots(10)
        .run()
        .collated_counts()
    )

    assert shots == {(("q", "1"),): 10}
