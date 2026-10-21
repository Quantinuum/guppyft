"""Guppy types and logical operations for the C4-Helix QEC architecture.

A Block contains two logical qubits, indexed 0 and 1. All code operations
act on blocks. TState is an opaque, consumable magic resource.
"""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.lang import owned
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys import Effect

from guppyft.code._util import logical_op
from guppyft.extensions import helix_ops, helix_types
from guppyft.std import LogicalMeasurement


@custom_type(helix_types.helix_block(), copyable=False, droppable=False)
class Block:
    """A block of two logical qubits, prepared as ``|00>`` by construction."""

    @hugr_op(logical_op(helix_ops.alloc_zero_def), effects=[Effect.ANY])
    @no_type_check
    def __new__() -> "Block":
        """Prepare a new Block resource."""

    @guppy
    @no_type_check
    def x(self: "Block", i: int) -> None:
        """Apply X."""
        x(self, i)

    @guppy
    @no_type_check
    def y(self: "Block", i: int) -> None:
        """Apply Y."""
        y(self, i)

    @guppy
    @no_type_check
    def z(self: "Block", i: int) -> None:
        """Apply Z."""
        z(self, i)

    @guppy
    @no_type_check
    def swap(self: "Block") -> None:
        """Exchange the two logical qubits."""
        swap(self)

    @guppy
    @no_type_check
    def cx(self: "Block") -> None:
        """Apply CX from qubit 0 to 1."""
        cx(self)

    @guppy
    @no_type_check
    def h_all(self: "Block") -> None:
        """Apply Hadamard to both qubits."""
        h_all(self)

    @guppy
    @no_type_check
    def cz(self: "Block") -> None:
        """Apply logical CZ."""
        cz(self)

    @guppy
    @no_type_check
    def ss(self: "Block") -> None:
        """Apply S to both logical qubits."""
        ss(self)

    @guppy
    @no_type_check
    def qec_cycle(self: "Block") -> None:
        """Perform a block QEC cycle."""
        qec_cycle(self)

    @guppy
    @no_type_check
    def measure_x_all(self: "Block" @ owned) -> LogicalMeasurement[2]:
        """Destructively measure both logical qubits in the X basis."""
        return measure_x_all(self)

    @guppy
    @no_type_check
    def measure_z_all(self: "Block" @ owned) -> LogicalMeasurement[2]:
        """Destructively measure both logical qubits in the Z basis."""
        return measure_z_all(self)

    @guppy
    @no_type_check
    def free(self: "Block" @ owned) -> None:
        """Discard this resource."""
        free(self)

    @guppy
    @no_type_check
    def t(self: "Block", i: int) -> None:
        """Apply T by preparing and consuming a magic resource."""
        t(self, i)

    @guppy
    @no_type_check
    def tdg(self: "Block", i: int) -> None:
        """Apply Tdg by preparing and consuming a magic resource."""
        tdg(self, i)


@custom_type(helix_types.helix_t_state(), copyable=False, droppable=False)
class TState:
    """A consumable T-state resource with backend-selected encoding."""

    @hugr_op(logical_op(helix_ops.prep_t_state_def), effects=[Effect.ANY])
    @no_type_check
    def __new__() -> "TState":
        """Prepare a new TState resource."""

    @guppy
    @no_type_check
    def free(self: "TState" @ owned) -> None:
        """Discard this resource."""
        free_t_state(self)


@hugr_op(logical_op(helix_ops.alloc_plus_def), effects=[Effect.ANY])
@no_type_check
def alloc_plus() -> Block:
    """Prepare the ``|++>`` state on a block."""


@hugr_op(logical_op(helix_ops.alloc_zero_def), effects=[Effect.ANY])
@no_type_check
def alloc_zero() -> Block:
    """Prepare the all-zero state on a block."""


@hugr_op(logical_op(helix_ops.cx_between_blocks_def))
@no_type_check
def cx_between_blocks(control: Block, target: Block, i: int, j: int) -> None:
    """Targeted CX from the first block to the second. Runtime indices select
    the control and target; the other qubits are unchanged.
    """


@hugr_op(logical_op(helix_ops.cx_def))
@no_type_check
def cx(block: Block) -> None:
    """CX from logical qubit 0 to 1."""


@hugr_op(logical_op(helix_ops.cx_transversal_def))
@no_type_check
def cx_transversal(control: Block, target: Block) -> None:
    """Apply CX from each logical qubit in the first block to the corresponding
    logical qubit in the second block.
    """


@hugr_op(logical_op(helix_ops.cz_def))
@no_type_check
def cz(block: Block) -> None:
    """Logical CZ."""


@hugr_op(logical_op(helix_ops.free_def), effects=[Effect.ANY])
@no_type_check
def free(block: Block @ owned) -> None:
    """Discard a block."""


@hugr_op(logical_op(helix_ops.free_t_state_def), effects=[Effect.ANY])
@no_type_check
def free_t_state(resource: TState @ owned) -> None:
    """Discard an unused T-state resource."""


@hugr_op(logical_op(helix_ops.h_all_def))
@no_type_check
def h_all(block: Block) -> None:
    """Hadamard on each logical qubit."""


@hugr_op(logical_op(helix_ops.inject_t_def))
@no_type_check
def inject_t(block: Block, i: int, resource: TState @ owned) -> None:
    """Consume a T-state resource and apply T to the logical qubit selected by a
    runtime index.
    """


@hugr_op(logical_op(helix_ops.inject_tdg_def))
@no_type_check
def inject_tdg(block: Block, i: int, resource: TState @ owned) -> None:
    """Consume a T-state resource and apply Tdg to the logical qubit selected by
    a runtime index.
    """


@hugr_op(logical_op(helix_ops.measure_x_all_def), effects=[Effect.ANY])
@no_type_check
def measure_x_all(block: Block @ owned) -> LogicalMeasurement[2]:
    """Destructively measure both logical qubits in the X basis."""


@hugr_op(logical_op(helix_ops.measure_z_all_def), effects=[Effect.ANY])
@no_type_check
def measure_z_all(block: Block @ owned) -> LogicalMeasurement[2]:
    """Destructively measure both logical qubits in the Z basis."""


@hugr_op(logical_op(helix_ops.prep_t_state_def), effects=[Effect.ANY])
@no_type_check
def prep_t_state() -> TState:
    """Create a resource that can be consumed to generate a T or Tdg operation
    on a logical qubit.
    """


@hugr_op(logical_op(helix_ops.qec_cycle_def))
@no_type_check
def qec_cycle(block: Block) -> None:
    """Perform syndrome extraction and recovery (or a Pauli-frame update).
    Ideally preserves the logical state, including external entanglement.
    """


@hugr_op(logical_op(helix_ops.ss_def))
@no_type_check
def ss(block: Block) -> None:
    """Logical S on both qubits."""


@hugr_op(logical_op(helix_ops.swap_def))
@no_type_check
def swap(block: Block) -> None:
    """Swap the two qubits in the block."""


@hugr_op(logical_op(helix_ops.x_def))
@no_type_check
def x(block: Block, i: int) -> None:
    """Apply X to the logical qubit selected by a runtime index."""


@hugr_op(logical_op(helix_ops.y_def))
@no_type_check
def y(block: Block, i: int) -> None:
    """Apply Y to the logical qubit selected by a runtime index."""


@hugr_op(logical_op(helix_ops.z_def))
@no_type_check
def z(block: Block, i: int) -> None:
    """Apply Z to the logical qubit selected by a runtime index."""


@guppy
def t(block: Block, i: int) -> None:
    """Apply T by preparing and consuming a magic resource."""
    resource = prep_t_state()
    inject_t(block, i, resource)


@guppy
def tdg(block: Block, i: int) -> None:
    """Apply Tdg by preparing and consuming a magic resource."""
    resource = prep_t_state()
    inject_tdg(block, i, resource)
