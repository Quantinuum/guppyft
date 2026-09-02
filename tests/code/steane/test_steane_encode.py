from typing import Any

import pytest
from guppylang import guppy
from guppylang.std.angles import pi
from guppylang.std.platform import output
from guppylang.std.quantum import (
    cx,
    discard,
    h,
    measure,
    qubit,
    rz,
    s,
    sdg,
    t,
    tdg,
    x,
    y,
    z,
)
from hugr import Hugr
from hugr.package import Package
from selene_hugr_qis_compiler import check_hugr

from guppyft.code.steane.encoder_spec import (
    QECPolicy,
    RUSStateFactoryConf,
    SteaneBuilder,
    SteaneEncoderParams,
)
from guppyft.encode import annotate_encoding


def test_encoder() -> None:

    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        x(q0)
        h(q1)
        z(q1)
        h(q1)
        cx(q0, q1)
        r0 = measure(q0).read()
        r1 = measure(q1).read()
        output("q0", r0)
        output("q1", r1)

    pkg = main.compile()
    res = (
        SteaneBuilder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=16)
        .run()
        .collated_shots()
    )

    assert res == [{"q0": [1], "q1": [0]}]


def test_encoder_smoke() -> None:

    @guppy
    def main() -> None:
        q0 = qubit()
        q1 = qubit()
        x(q0)
        y(q0)
        z(q0)
        h(q0)
        s(q0)
        sdg(q0)
        cx(q0, q1)
        output("q0", measure(q0).read())
        discard(q1)

    SteaneBuilder().build(n_blocks=2).emulator(main.compile(), n_qubits=16).run()


def test_encode_function_call() -> None:
    # `foo` is a public function, so the `ReplaceEncoder` pass (which defaults to
    # `GlobalScope.PRESERVE_PUBLIC`) should in principle leave its interface/behaviour
    # untouched. However, `PRESERVE_PUBLIC` is not actually enforced by the underlying
    # `ReplaceTypes` pass (a lowering pass, which ignores `preserve_interface` since its
    # purpose is to change signatures) - it still rewrites ops/types in `foo` like
    # everything else. This test just checks that the call to `foo` is still valid
    # after encoding, not that `foo`'s public interface was preserved.
    @guppy
    def main() -> None:
        q = qubit()
        foo(q)
        discard(q)

    @guppy
    def foo(q: qubit) -> None:
        pass

    pkg = main.compile()
    phys_pkg = SteaneBuilder().build(n_blocks=1).encode(pkg)

    check_hugr(phys_pkg.to_bytes())


def test_encoder_missing_op() -> None:
    # `tket.quantum.rz` has no replacement registered in `SteaneBuilder`, so the encoder
    # leaves it untouched while everything else is lowered to logical qubits. This
    # mismatch causes `rz`'s (unencoded) qubit port to be connected to an (encoded)
    # logical qubit port, which fails validation.
    @guppy
    def main() -> None:
        q = qubit()
        rz(q, pi / 2)
        discard(q)

    pkg = main.compile()
    with pytest.raises(
        ValueError,
        match=(
            r"Error encoding `tket.quantum.Y` at node Node\(7\). "
            r"Operation not yet supported during encoding."
        ),
    ):
        SteaneBuilder().build(n_blocks=1).encode(pkg)


def test_builder_methods() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        output("q", measure(q).read())

    pkg = main.compile()

    my_policy = QECPolicy(threshold=1)
    my_policy.set_cost("X", 1.0)

    zero_factory_conf = RUSStateFactoryConf(1, 2)

    res = (
        SteaneBuilder()
        .with_qec_policy(my_policy)
        .with_zero_factory_conf(zero_factory_conf)
        .build(n_blocks=1)
        .emulator(pkg, n_qubits=20)
        .run()
        .collated_shots()
    )

    assert res == [{"q": [1]}]


def test_encoder_control_flow() -> None:
    @guppy
    def main() -> None:
        q0 = qubit()
        if measure(q0).read():  # noqa: SIM108
            q1 = qubit()
        else:
            q1 = qubit()

        output("q1", measure(q1).read())

    pkg = main.compile()
    res = (
        SteaneBuilder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=20)
        .run()
        .collated_shots()
    )

    assert res == [{"q1": [0]}]


def test_annotate_steane_encoding() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    annotate_encoding(pkg, SteaneEncoderParams(n_blocks=4))

    assert hugr[hugr.module_root].metadata["guppyft.encoding"] == {
        "encoding": "steane",
        "params": {"n_blocks": 4},
    }


def test_t_encoder_smoke() -> None:
    @guppy
    def main() -> None:
        q = qubit()
        t(q)
        discard(q)
        q = qubit()
        tdg(q)
        discard(q)

    res = (
        SteaneBuilder()
        .build(n_blocks=2)
        .emulator(main.compile(), n_qubits=17)
        .run()
        .collated_shots()
    )

    assert res == [{}]


def test_encode_classical() -> None:
    @guppy
    def main() -> None:
        pass

    res = (
        SteaneBuilder()
        .build(n_blocks=1)
        .emulator(main.compile(), n_qubits=1)
        .run()
        .collated_shots()
    )
    assert res == [{}]
