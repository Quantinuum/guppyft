import pytest
from zixy.qubit import pauli

from guppyft.verifier.code import (
    CodeDefinitionError,
    StabilizerCode,
)

from .ops.steane import STEANE_DEF


def test_steane_y_logicals() -> None:
    assert str(STEANE_DEF.y_logicals) == "(-1, Y0 Y1 Y2 Y3 Y4 Y5 Y6)"
    assert isinstance(STEANE_DEF.y_logicals, pauli.SignTerms)


def test_code_validation() -> None:

    with pytest.raises(
        CodeDefinitionError,
        match=r"The number of stabilizer generators must equal n-k."
        + r" Got n=4, k=2 with 4 generators.",
    ):
        StabilizerCode.from_strings(
            4,
            2,
            2,
            generators=["XXXX", "ZZZZ", "YIII", "IIXZ"],  # fake generators
            x_logicals=["XXII", "XIXI"],
            z_logicals=["IZIZ", "IIZZ"],
        )

    with pytest.raises(
        CodeDefinitionError,
        match=r"Incorrect number of X logical operators: expected 2, got 3.",
    ):
        StabilizerCode.from_strings(
            4,
            2,
            2,
            generators=["XXXX", "ZZZZ"],
            x_logicals=["XXII", "XIXX", "XXXI"],  # fake x_logicals
            z_logicals=["IZIZ", "IIZZ"],
        )

    with pytest.raises(
        CodeDefinitionError,
        match="All of the stabilizer generators must commute!",
    ):
        StabilizerCode.from_strings(
            4,
            2,
            2,
            generators=["XXXX", "XZZZ"],  # fake generators
            x_logicals=["XXII", "XIXI"],
            z_logicals=["IZIZ", "IIZZ"],
        )
