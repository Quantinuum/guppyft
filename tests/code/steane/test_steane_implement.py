from collections.abc import Callable

from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.platform import result
from hugr.ops import ExtOp

from guppyft.code.steane.encode import SteaneInstance
from guppyft.code.steane.logical import Qubit, cx, h, measure_z, x, z


def test_qalloc_measure(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = make_steane_instance(1).implement_ops(pkg, as_bytes=True)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=8).run().collated_shots()

    assert res == [{"res": [0]}]


def test_x(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        x(q)
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = make_steane_instance(1).implement_ops(pkg, as_bytes=True)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=8).run().collated_shots()

    assert res == [{"res": [1]}]


def test_h_z(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        h(q)
        z(q)
        h(q)
        result("res", measure_z(q).decode())

    pkg = main.compile()
    phys_pkg = make_steane_instance(1).implement_ops(pkg, as_bytes=True)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=8).run().collated_shots()

    assert res == [{"res": [1]}]


def test_cx(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q0, q1 = Qubit(), Qubit()
        x(q0)
        cx(q0, q1)
        result("q0", measure_z(q0).decode())
        result("q1", measure_z(q1).decode())

    pkg = main.compile()
    phys_pkg = make_steane_instance(2).implement_ops(pkg, as_bytes=True)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=18).run().collated_shots()

    assert res == [{"q0": [1], "q1": [1]}]


def test_qec_cycle(make_steane_instance: Callable[[int], SteaneInstance]) -> None:

    @guppy
    def main() -> None:
        q = Qubit()
        q.qec_cycle()
        result("q", q.measure_z().decode())

    pkg = main.compile()
    phys_pkg = make_steane_instance(1).implement_ops(pkg)

    hugr = phys_pkg.modules[0]
    qec_cycle = next(
        node
        for node, node_data in hugr.items()
        if getattr(node_data.op, "f_name", None) == "link.guppyft.steane.ops.qec_cycle"
    )
    assert any(
        isinstance(hugr[node].op, ExtOp) and "tket.globals.map" in hugr[node].op.name()
        for node in hugr.descendants(qec_cycle)
    )

    res = EmulatorBuilder().build(phys_pkg, n_qubits=15).run().collated_shots()

    assert res == [{"q": [0]}]
