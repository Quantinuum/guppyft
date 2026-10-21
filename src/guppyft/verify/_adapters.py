"""Adapt Clifford implementations to the arrays used to prepare Choi states.

Array arguments precede the implementation so Guppy can infer the block size
before instantiating a generic implementation's function type.
"""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.builtins import array
from guppylang.std.lang import Function, owned
from guppylang.std.quantum import qubit

from guppyft.std import LogicalBlock

N = guppy.nat_var("N")


@guppy
@no_type_check
def _from_array(qs: array[qubit, N] @ owned) -> LogicalBlock[N]:
    """Wrap physical qubits in a logical block without changing their order."""
    return LogicalBlock(qs)


@guppy
@no_type_check
def _logical_block_to_array(block: LogicalBlock[N] @ owned) -> array[qubit, N]:
    """Consume a logical block and return its physical qubit array."""
    return block.data_qs


@guppy
@no_type_check
def _array_to_array(qs: array[qubit, N] @ owned) -> array[qubit, N]:
    return qs


@guppy.overload(_array_to_array, _logical_block_to_array)
@no_type_check
def _to_array(block):
    """Consume an array or LogicalBlock and return its physical qubit array."""


@guppy
@no_type_check
def _apply_single_array(
    qs: array[qubit, N] @ owned,
    implementation: Function[[array[qubit, N]], None],
) -> array[qubit, N]:
    implementation(qs)
    return qs


@guppy
@no_type_check
def _apply_single_logical_block(
    qs: array[qubit, N] @ owned,
    implementation: Function[[LogicalBlock[N]], None],
) -> array[qubit, N]:
    block = _from_array(qs)
    implementation(block)
    return _to_array(block)


@guppy.overload(_apply_single_array, _apply_single_logical_block)
@no_type_check
def apply_single_block(qs, implementation):
    """Select the block representation from the implementation's argument type."""


@guppy
@no_type_check
def _apply_double_array(
    first: array[qubit, N] @ owned,
    second: array[qubit, N] @ owned,
    implementation: Function[[array[qubit, N], array[qubit, N]], None],
) -> tuple[array[qubit, N], array[qubit, N]]:
    implementation(first, second)
    return first, second


@guppy
@no_type_check
def _apply_double_logical_block(
    first: array[qubit, N] @ owned,
    second: array[qubit, N] @ owned,
    implementation: Function[[LogicalBlock[N], LogicalBlock[N]], None],
) -> tuple[array[qubit, N], array[qubit, N]]:
    first_block = _from_array(first)
    second_block = _from_array(second)
    implementation(first_block, second_block)
    return _to_array(first_block), _to_array(second_block)


@guppy.overload(_apply_double_array, _apply_double_logical_block)
@no_type_check
def apply_double_block(first, second, implementation):
    """Adapt two arrays to the representation expected by a two-block operation."""
