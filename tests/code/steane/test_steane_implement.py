from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.platform import result

from guppyft.code.steane.encoder_spec import SteaneSpec
from guppyft.logical.steane import Qubit, cx, h, measure_z, x, z


def test_qalloc_measure() -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [[0]]}]


def test_x() -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        x(q)
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [[1]]}]


def test_h_z() -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        h(q)
        z(q)
        h(q)
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [[1]]}]


def test_cx() -> None:

    @guppy
    def main() -> None:
        q0, q1 = Qubit(), Qubit()
        x(q0)
        cx(q0, q1)
        result("q0", measure_z(q0).decode())
        result("q1", measure_z(q1).decode())

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=2).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=14).run().collated_shots()

    assert res == [{"q0": [[1]], "q1": [[1]]}]
