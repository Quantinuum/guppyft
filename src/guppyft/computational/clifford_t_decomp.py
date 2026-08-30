from typing import no_type_check

from guppylang import guppy
from guppylang.std.quantum import cx, h, qubit, t, tdg


@guppy
@no_type_check
def toffoli(ctrl0: qubit, ctrl1: qubit, target: qubit) -> None:
    """Implement a Toffoli gate via decomposition into 7 T gates."""
    h(target)
    cx(ctrl1, target)
    tdg(target)
    cx(ctrl0, target)
    t(target)
    cx(ctrl1, target)
    tdg(target)
    cx(ctrl0, target)
    t(ctrl1)
    t(target)
    h(target)
    cx(ctrl0, ctrl1)
    t(ctrl0)
    tdg(ctrl1)
    cx(ctrl0, ctrl1)
