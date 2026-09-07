"""Guppy runtime math functions.

Duplicated from guppy-algos to avoid circular imports.
These should be added to guppylang.
    (https://github.com/Quantinuum/guppylang/issues/1204)

Original contribution: @vvandaele (Vivien Vandaele)
"""

from typing import no_type_check

from guppylang import guppy


@guppy
@no_type_check
def get_bit(k: int, i: int) -> bool:
    """Extract bit i from integer k.

    Args:
        k: Integer value.
        i: Bit position, where 0 is the rightmost (least significant) bit.

    Returns:
        bool: True if bit i is 1, False otherwise.

    """
    return ((k >> i) & 1) == 1


@guppy
@no_type_check
def floor(x: float) -> int:
    """Compute the largest integer less than or equal to x.

    Args:
        x: Floating-point value.

    Returns:
        int: Largest integer less than or equal to x.

    """
    i = int(x)
    if float(i) > x:
        return i - 1
    return i


@guppy
@no_type_check
def tan(x: float) -> float:
    """Compute the tangent of x.

    Based on https://go.dev/src/math/tan.go.

    Args:
        x: Angle in radians.

    Returns:
        float: Tangent of x.

    """
    pi4a = 7.85398125648498535156e-1
    pi4b = 3.77489470793079817668e-8
    pi4c = 2.69515142907905952645e-15
    m4pi = 1.27323954473516268615e0
    tp0 = -1.30936939181383777646e4
    tp1 = 1.15351664838587416140e6
    tp2 = -1.79565251976484877988e7
    tq1 = 1.36812963470692954678e4
    tq2 = -1.32089234440210967447e6
    tq3 = 2.50083801823357915839e7
    tq4 = -5.38695755929454629881e7
    sign = False

    if x < 0:
        x = -x
        sign = True
    j = int(x * m4pi)
    y = float(j)
    if j & 1 == 1:
        j = j + 1
        y = y + 1.0
    z = ((x - y * pi4a) - y * pi4b) - y * pi4c
    zz = z * z
    if zz > 1e-14:
        y = z + z * (
            zz
            * (
                ((tp0 * zz + tp1) * zz + tp2)
                / ((((zz + tq1) * zz + tq2) * zz + tq3) * zz + tq4)
            )
        )
    else:
        y = z
    if j & 2 == 2:
        y = -1.0 / y
    if sign:
        y = -y
    return y
