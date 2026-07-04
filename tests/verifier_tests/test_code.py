import pytest
from zixy.qubit import pauli

from guppyft.verifier.code import (
    CodeDefinitionError,
    StabilizerCode,
)

from .ops.iceberg import (
    ICEBERG_GENERATORS,
    ICEBERG_X_LOGICAL,
    ICEBERG_Z_LOGICAL,
)
from .ops.steane import STEANE_DEF


def test_steane_y_logicals() -> None:
    assert str(STEANE_DEF.y_logicals) == "(-1, Y0 Y1 Y2 Y3 Y4 Y5 Y6)"
    assert isinstance(STEANE_DEF.y_logicals, pauli.SignTerms)


def test_code_validation() -> None:

    fake_generators1 = pauli.StringSet.from_cmpnts(
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
            x_logicals=ICEBERG_X_LOGICAL,
            z_logicals=ICEBERG_Z_LOGICAL,
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
            generators=ICEBERG_GENERATORS,
            x_logicals=fake_x_logicals,
            z_logicals=ICEBERG_Z_LOGICAL,
        )

    fake_generators2 = pauli.StringSet.from_cmpnts(
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
            x_logicals=ICEBERG_X_LOGICAL,
            z_logicals=ICEBERG_Z_LOGICAL,
        )
