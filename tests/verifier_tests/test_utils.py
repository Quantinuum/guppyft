from selene_stim_plugin.state import Stabilizer, StabilizerList
from zixy.qubit import pauli
from zixy.qubit.pauli import I, X, Z

from guppyft.verifier.utils import (
    selene_stabilizer_to_zixy_signterm,
    stabilizerlist_to_signterms,
    string_to_unit_stringset,
    unit_length_strings_to_string,
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


def test_stringset_to_string() -> None:
    STEANE_X_LOGICAL = pauli.Strings.from_iterable(((X, X, X, X, X, X, X),), 7)
    my_string = unit_length_strings_to_string(STEANE_X_LOGICAL, string_capacity=7)
    expected_string = pauli.String.from_str("X0 X1 X2 X3 X4 X5 X6")
    assert my_string == expected_string


def test_stringset_to_string2() -> None:
    xi_stringset = pauli.Strings.from_iterable(((X, X, I, I, I, I, I),), 7)
    my_string = unit_length_strings_to_string(xi_stringset, string_capacity=7)
    expected_string = pauli.String.from_str("X0 X1 I2 I3 I4 I5 I6", 7)
    assert my_string == expected_string


def test_string_to_stringset() -> None:
    BITFLIP_Z_LOGICAL = pauli.String.from_str("Z0 I1 I2")
    my_stringset = string_to_unit_stringset(BITFLIP_Z_LOGICAL)
    expected_stringset = pauli.StringSet.from_iterable(((Z, I, I),), 3)
    assert my_stringset == expected_stringset
