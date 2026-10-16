"""Guppy types and logical operations for the C4-Helix QEC architecture.

A Block contains two logical qubits, indexed 0 and 1. All code operations
act on blocks. TState is an opaque, consumable magic resource.
These bindings define logical operations; physical lowering is backend-specific.
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
    """A block of two logical qubits, prepared as |00> by construction."""

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
    def cx_swap(self: "Block") -> None:
        """Apply CX from qubit 0 to 1, then exchange them."""
        cx_swap(self)

    @guppy
    @no_type_check
    def hh_swap(self: "Block") -> None:
        """Apply Hadamard to both qubits, then exchange them."""
        hh_swap(self)

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
    def measure_xx(self: "Block" @ owned) -> LogicalMeasurement[2]:
        """Destructively measure both logical qubits in the X basis."""
        return measure_xx(self)

    @guppy
    @no_type_check
    def measure_zz(self: "Block" @ owned) -> LogicalMeasurement[2]:
        """Destructively measure both logical qubits in the Z basis."""
        return measure_zz(self)

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
        """Apply T dagger by preparing and consuming a magic resource."""
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
    """Bind the `alloc_plus` logical operation.

    Prepare the |++> state on a block.
    """


@hugr_op(logical_op(helix_ops.alloc_zero_def), effects=[Effect.ANY])
@no_type_check
def alloc_zero() -> Block:
    """Bind the `alloc_zero` logical operation.

    Prepare the all-zero state on a block.
    """


@hugr_op(logical_op(helix_ops.cx_between_blocks_def))
@no_type_check
def cx_between_blocks(control: Block, target: Block, i: int, j: int) -> None:
    """Bind the `cx_between_blocks` logical operation.

    Targeted CX from the first block to the second. Runtime indices select the
    control and target; the other qubits are unchanged.
    """


@hugr_op(logical_op(helix_ops.cx_swap_def))
@no_type_check
def cx_swap(block: Block) -> None:
    """Bind the `cx_swap` logical operation.

    CX from logical qubit 0 to 1, then SWAP: |a,b> -> |a XOR b,a>.
    """


@hugr_op(logical_op(helix_ops.cx_transversal_def))
@no_type_check
def cx_transversal(control: Block, target: Block) -> None:
    """Bind the `cx_transversal` logical operation.

    Apply CX from each logical qubit in the first block to the corresponding
    logical qubit in the second block, preserving block order.
    """


@hugr_op(logical_op(helix_ops.cz_def))
@no_type_check
def cz(block: Block) -> None:
    """Bind the `cz` logical operation.

    Logical CZ: |a,b> -> (-1)^(ab)|a,b>. Lowering must compensate the physical
    gadget's residual Z on qubit 1.
    """


@hugr_op(logical_op(helix_ops.free_def), effects=[Effect.ANY])
@no_type_check
def free(block: Block @ owned) -> None:
    """Bind the `free` logical operation.

    Discard a block in any logical state.
    """


@hugr_op(logical_op(helix_ops.free_t_state_def), effects=[Effect.ANY])
@no_type_check
def free_t_state(resource: TState @ owned) -> None:
    """Bind the `free_t_state` logical operation.

    Discard an unused T-state resource.
    """


@hugr_op(logical_op(helix_ops.hh_swap_def))
@no_type_check
def hh_swap(block: Block) -> None:
    """Bind the `hh_swap` logical operation.

    Hadamard on each logical qubit followed by SWAP.
    """


@hugr_op(logical_op(helix_ops.inject_t_def))
@no_type_check
def inject_t(block: Block, i: int, resource: TState @ owned) -> None:
    """Bind the `inject_t` logical operation.

    Consume a T-state resource and apply T = diag(1, exp(i*pi/4)) to the logical
    qubit selected by a runtime index, preserving its block partner. Inputs are
    (block, index, resource); measurement and feed-forward corrections are
    included, leaving no outstanding Clifford correction.
    """


@hugr_op(logical_op(helix_ops.inject_tdg_def))
@no_type_check
def inject_tdg(block: Block, i: int, resource: TState @ owned) -> None:
    """Bind the `inject_tdg` logical operation.

    Consume the same T-state resource as inject_t and apply T dagger to the
    indexed logical qubit, preserving its block partner. Inputs are (block,
    index, resource); all measurement and Clifford corrections are included.
    """


@hugr_op(logical_op(helix_ops.measure_xx_def), effects=[Effect.ANY])
@no_type_check
def measure_xx(block: Block @ owned) -> LogicalMeasurement[2]:
    """Bind the `measure_xx` logical operation.

    Destructively measure both logical qubits in the X basis. Return a two-
    outcome logical measurement, ordered by logical index. Decoded bit b denotes
    eigenvalue (-1)^b; this is not an XX parity measurement.
    """


@hugr_op(logical_op(helix_ops.measure_zz_def), effects=[Effect.ANY])
@no_type_check
def measure_zz(block: Block @ owned) -> LogicalMeasurement[2]:
    """Bind the `measure_zz` logical operation.

    Destructively measure both logical qubits in the Z basis. Return a two-
    outcome logical measurement, ordered by logical index. Decoded bit b denotes
    eigenvalue (-1)^b; this is not a ZZ parity measurement.
    """


@hugr_op(logical_op(helix_ops.prep_t_state_def), effects=[Effect.ANY])
@no_type_check
def prep_t_state() -> TState:
    """Bind the `prep_t_state` logical operation.

    Supply a resource with ideal state (|0> + exp(i*pi/4)|1>)/sqrt(2). The
    backend chooses the factory and encoding, and handles heralded retries.
    Preparation need not occur inside a Helix block.
    """


@hugr_op(logical_op(helix_ops.qec_cycle_def))
@no_type_check
def qec_cycle(block: Block) -> None:
    """Bind the `qec_cycle` logical operation.

    Perform syndrome extraction and recovery (or a Pauli-frame update). Ideally
    preserves the logical state, including external entanglement.
    """


@hugr_op(logical_op(helix_ops.ss_def))
@no_type_check
def ss(block: Block) -> None:
    """Bind the `ss` logical operation.

    Logical S on both qubits: |a,b> -> i^(a+b)|a,b>. Lowering must compensate
    the physical gadget's residual Z on both qubits and include the flagging and
    syndrome extraction required for fault tolerance.
    """


@hugr_op(logical_op(helix_ops.swap_def))
@no_type_check
def swap(block: Block) -> None:
    """Bind the `swap` logical operation.

    Swap the two qubits in the block.
    """


@hugr_op(logical_op(helix_ops.x_def))
@no_type_check
def x(block: Block, i: int) -> None:
    """Bind the `x` logical operation.

    Apply X to the logical qubit selected by a runtime index.
    """


@hugr_op(logical_op(helix_ops.y_def))
@no_type_check
def y(block: Block, i: int) -> None:
    """Bind the `y` logical operation.

    Apply Y to the logical qubit selected by a runtime index.
    """


@hugr_op(logical_op(helix_ops.z_def))
@no_type_check
def z(block: Block, i: int) -> None:
    """Bind the `z` logical operation.

    Apply Z to the logical qubit selected by a runtime index.
    """


@guppy
def t(block: Block, i: int) -> None:
    """Apply T by preparing and consuming a magic resource."""
    resource = prep_t_state()
    inject_t(block, i, resource)


@guppy
def tdg(block: Block, i: int) -> None:
    """Apply T dagger by preparing and consuming a magic resource."""
    resource = prep_t_state()
    inject_tdg(block, i, resource)
