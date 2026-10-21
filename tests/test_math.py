"""Tests for Guppy runtime math functions.

Duplicated from guppy-algos to avoid circular imports.
These should be added to guppylang.
    (https://github.com/Quantinuum/guppylang/issues/1204)

Original contribution: @vvandaele (Vivien Vandaele)
"""

from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.std.builtins import output

from guppyft._math import floor, get_bit


@pytest.mark.parametrize(
    ("k", "i", "expected"),
    [
        (5, 0, True),
        (5, 1, False),
        (0, 0, False),
        (-1, 0, True),
        (-1, 5, True),
        (-2, 0, False),
    ],
)
def test_get_bit(k: int, i: int, expected: bool) -> None:
    """Test get_bit extracts correct bits from integers."""

    @guppy
    @no_type_check
    def test_circuit() -> None:
        output("bit", get_bit(k, i))

    res = test_circuit.emulator(1).run()
    assert res.collated_shots()[0]["bit"][0] == expected


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (3.7, 3),
        (-3.7, -4),
        (4.0, 4),
    ],
)
def test_floor(x: float, expected: int) -> None:
    """Test floor computes correct integer floors."""

    @guppy
    @no_type_check
    def test_circuit() -> None:
        output("floor_val", floor(x))

    res = test_circuit.emulator(1).run()
    assert res.collated_shots()[0]["floor_val"][0] == expected
