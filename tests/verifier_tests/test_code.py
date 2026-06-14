import pytest
from zixy.qubit import pauli
from zixy.qubit.pauli import I, X, Z

from guppyft.verifier.code import (
    ICEBERG_4_2_2,
    ICEBERG_4_2_2_GENERATORS,
    ICEBERG_4_2_2_X,
    ICEBERG_4_2_2_Z,
    STEANE,
    CodeDefinitionError,
    StabilizerCode,
)


def test_iceberg_stabilizers() -> None:
    assert (
        len(ICEBERG_4_2_2.generators)
        == ICEBERG_4_2_2.num_physical_qubits - ICEBERG_4_2_2.num_logical_qubits
    )


def test_iceberg_logicals() -> None:
    assert ICEBERG_4_2_2.x_logicals[0].get_tuple() == (X, X, I, I)
    assert ICEBERG_4_2_2.x_logicals[1].get_tuple() == (X, I, X, I)
    assert ICEBERG_4_2_2.z_logicals[0].get_tuple() == (I, Z, I, Z)
    assert ICEBERG_4_2_2.z_logicals[1].get_tuple() == (I, I, Z, Z)


def test_steane_y_logicals() -> None:
    assert str(STEANE.y_logicals) == "(-1, Y0 Y1 Y2 Y3 Y4 Y5 Y6)"


def test_code_validation() -> None:

    fake_generators1 = pauli.StringSet.from_strings(
        pauli.Strings.from_str(
            "X0 X1 X2 X3, Z0 Z1 Z2 Z3, Y0, Z2 X1",
            4,
        )
    )
    with pytest.raises(
        CodeDefinitionError,
        match=r"The number of stabilizer generators must equal n-k."
        + r" Got n=4, k=2 with 4 generators.",
    ):
        StabilizerCode(
            4,
            2,
            2,
            generators=fake_generators1,
            x_logicals=ICEBERG_4_2_2_X,
            z_logicals=ICEBERG_4_2_2_Z,
        )

    fake_x_logicals = pauli.Strings.from_str(
        "X0 X1 I2 I3, X0 I1 X2 X3, X0 X1 X2 I3",
        4,
    )

    with pytest.raises(
        CodeDefinitionError,
        match=r"Incorrect number of X logical operators: expected 2, got 3.",
    ):
        StabilizerCode(
            4,
            2,
            2,
            generators=ICEBERG_4_2_2_GENERATORS,
            x_logicals=fake_x_logicals,
            z_logicals=ICEBERG_4_2_2_Z,
        )

    fake_generators2 = pauli.StringSet.from_strings(
        pauli.Strings.from_str(
            "X0 X1 X2 X3, X0 Z1 Z2 Z3",
            4,
        )
    )
    with pytest.raises(
        CodeDefinitionError,
        match="All of the stabilizer generators must commute!",
    ):
        StabilizerCode(
            4,
            2,
            2,
            generators=fake_generators2,
            x_logicals=ICEBERG_4_2_2_X,
            z_logicals=ICEBERG_4_2_2_Z,
        )
