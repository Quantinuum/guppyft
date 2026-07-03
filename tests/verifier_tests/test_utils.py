from selene_stim_plugin.state import Stabilizer, StabilizerList
from zixy.qubit import pauli

from guppyft.verifier.utils import (
    selene_stabilizer_to_zixy_signterm,
    stabilizerlist_to_signterms,
)


def test_selene_to_zixy() -> None:
    stab = Stabilizer("-XZXXY")
    converted_op = selene_stabilizer_to_zixy_signterm(stab)
    assert isinstance(converted_op, pauli.SignTerm)
    assert str(converted_op) == "(-1, X0 Z1 X2 X3 Y4)"


def test_stabilizer_list_to_stringset() -> None:
    stab_list = StabilizerList(["-XZXXY", "+XZZZY", "-ZXXXY"])
    signterms = stabilizerlist_to_signterms(stab_list)
    assert isinstance(signterms, pauli.SignTerms)
    assert (
        str(signterms)
        == "(-1, X0 Z1 X2 X3 Y4), (+1, X0 Z1 Z2 Z3 Y4), (-1, Z0 X1 X2 X3 Y4)"
    )
