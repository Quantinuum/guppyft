from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.platform import result

from guppyft.encode import (
    implement_ops,
)
from guppyft.logical.steane import Qubit, measure_z

from .util import steane_spec


def test_qalloc_measure() -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        result("res", measure_z(q).decode())

    pkg = main.compile()

    implemented_pkg = implement_ops(pkg, steane_spec)
    res = EmulatorBuilder().build(implemented_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [[0]]}]
