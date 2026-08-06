from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.builtins import result
from guppylang.std.quantum import measure, qubit

from guppyft.code.steane.encoder_spec import SteaneSpec


def test_encoder() -> None:

    @guppy
    def main() -> None:
        q = qubit()
        res = measure(q).read()
        result("res", res)

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [0]}]
