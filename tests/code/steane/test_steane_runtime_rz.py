from typing import no_type_check

from guppylang import guppy
from guppylang.std.angles import pi
from guppylang.std.platform import output
from guppylang.std.quantum import (
    discard,
    h,
    qubit,
    rz,
)
from selene_sim import Coinflip

from guppyft.code.steane.encoder_spec import (
    SteaneBuilder,
)
from guppyft.logical._comparator_based_rz import (
    comparator_based_rz_cascade,
    n_comparator_based_rz_cascade_ancillas,
)


def test_encode_rz_decomposition() -> None:

    epsilon = 0.01
    rz_fn = comparator_based_rz_cascade(epsilon)

    @guppy
    @no_type_check
    def main() -> None:
        target = qubit()
        h(target)
        rz_fn(target, pi / 16)
        discard(target)
        output("success", 1)

    # Original block + one block for magic + ancilla space for Rz
    n_blocks = 1 + 1 + n_comparator_based_rz_cascade_ancillas(epsilon)
    pkg = main.compile()
    res = (
        SteaneBuilder()
        .build(n_blocks=n_blocks)
        .emulator(pkg, n_qubits=7 * n_blocks + 6)
        .with_simulator(Coinflip(bias=0.0))
        .run()
        .collated_shots()
    )

    assert res == [{"success": [1]}]


def test_encode_rz_directly() -> None:

    epsilon = 0.01

    @guppy
    @no_type_check
    def main() -> None:
        target = qubit()
        h(target)
        rz(target, pi / 16)
        discard(target)
        output("success", 1)

    # Original block + one block for magic + ancilla space for Rz
    n_blocks = 1 + 1 + n_comparator_based_rz_cascade_ancillas(epsilon)
    pkg = main.compile()
    res = (
        SteaneBuilder()
        .build(n_blocks=n_blocks)
        .emulator(pkg, n_qubits=7 * n_blocks + 6)
        .with_simulator(Coinflip(bias=0.0))
        .run()
        .collated_shots()
    )

    assert res == [{"success": [1]}]
