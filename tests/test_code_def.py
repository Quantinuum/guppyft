import pytest
from zixy.qubit import pauli

from guppyft.code_def import (
    CodeDefinitionError,
    StabilizerCode,
)


def test_steane_y_logicals() -> None:

    STEANE_DEF = StabilizerCode.from_python_strings(
        num_physical_qubits=7,
        num_logical_qubits=1,
        distance=3,
        generators=["XXXXIII", "IXXIXXI", "IIXXIXX", "ZZZZIII", "IZZIZZI", "IIZZIZZ"],
        x_logicals=["XXXXXXX"],
        z_logicals=["ZZZZZZZ"],
    )

    assert str(STEANE_DEF.y_logicals) == "(-1, Y0 Y1 Y2 Y3 Y4 Y5 Y6)"
    assert isinstance(STEANE_DEF.y_logicals, pauli.SignTerms)


def test_code_validation() -> None:

    with pytest.raises(
        CodeDefinitionError,
        match=r"The number of stabilizer generators must equal n-k."
        + r" Got n=4, k=2 with 4 generators.",
    ):
        StabilizerCode.from_python_strings(
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
        StabilizerCode.from_python_strings(
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
        StabilizerCode.from_python_strings(
            4,
            2,
            2,
            generators=["XXXX", "XZZZ"],  # fake generators
            x_logicals=["XXII", "XIXI"],
            z_logicals=["IZIZ", "IIZZ"],
        )

    with pytest.raises(
        CodeDefinitionError,
        match="All Pauli strings must be of length",
    ):
        StabilizerCode.from_python_strings(
            4,
            2,
            2,
            generators=["XXXX", "ZZZZ"],
            x_logicals=["XXII", "XIXI"],
            z_logicals=["IZI", "IIZZ"],  # fake z_logical
        )

    with pytest.raises(
        CodeDefinitionError,
        match="All Pauli strings must be defined over the alphabet",
    ):
        StabilizerCode.from_python_strings(
            4,
            2,
            2,
            generators=["X_XX", "ZZZZ"],  # fake generators
            x_logicals=["XXII", "XIXI"],
            z_logicals=["IZIZ", "IIZZ"],
        )
