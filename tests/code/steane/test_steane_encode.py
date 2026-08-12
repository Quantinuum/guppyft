import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.platform import output
from guppylang.std.quantum import discard, measure, qubit, y
from selene_hugr_qis_compiler import check_hugr

from guppyft.code.steane.encoder_spec import SteaneSpec


def test_encoder() -> None:

    @guppy
    def main() -> None:
        q = qubit()
        r = measure(q).read()
        output("res", r)

    pkg = main.compile()
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=7).run().collated_shots()

    assert res == [{"res": [0]}]


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
    phys_pkg = SteaneSpec(n_blocks=1).encode(pkg)

    check_hugr(phys_pkg.to_bytes())


def test_encoder_missing_op() -> None:
    # `tket.quantum.y` has no replacement registered in `SteaneSpec`, so the encoder
    # leaves it untouched while everything else is lowered to logical qubits. This
    # mismatch causes `y`'s (unencoded) qubit port to be connected to an (encoded)
    # logical qubit port, which fails validation.
    @guppy
    def main() -> None:
        q = qubit()
        y(q)
        discard(q)

    pkg = main.compile()
    with pytest.raises(
        ValueError,
        match=(
            r"Encoded Hugr failed validation: Connected ports "
            r"Port\(Outgoing, 0\) in Node\(4\) and Port\(Incoming, 0\) in Node\(5\) "
            r"have incompatible kinds\. Cannot connect qubit to qubit\."
        ),
    ):
        SteaneSpec(n_blocks=1).encode(pkg)


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
    phys_pkg = SteaneSpec(n_blocks=2).encode(pkg)
    res = EmulatorBuilder().build(phys_pkg, n_qubits=20).run().collated_shots()

    assert res == [{"q1": [0]}]
