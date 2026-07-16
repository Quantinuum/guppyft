from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.quantum import measure, qubit

from guppyft.encode import encode
from tests.code.steane.util import enc_spec


def test_encoder() -> None:

    @guppy
    def main() -> None:
        q = qubit()
        _res = measure(q).read()
        # TODO result does not work as `res` is of type bool in the
        #  computational program, but the decode op converts it into
        #  `array[bool, 1]`.
        # result("res", res)

    pkg = main.compile()
    phys_pkg = encode(pkg, spec=enc_spec)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{}]
