from guppylang import guppy
from guppylang.std.platform import output
from guppylang.std.quantum import (
    cx,
    h,
    measure,
    qubit,
    x,
    z,
)
from selene_hugr_qis_compiler import check_hugr

from guppyft.code.steane.encode import (
    SteaneBuilder,
)


def test_steane_compiler() -> None:

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
    pkg = SteaneBuilder().build(n_blocks=2).compile(pkg)
    check_hugr(pkg.to_bytes())
    assert "tket.quantum" not in [ext.name for ext in pkg.extensions]
