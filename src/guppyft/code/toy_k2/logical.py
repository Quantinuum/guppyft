"""Guppy functions for the logical operations and types for the ToyK2 QEC architecture.

This module contains bindings for the fundamental ops in the HUGR extensions, as well
as composite operations that comprise multiple logical operations.

The physical implementation for these ops is provided in
:py:mod:`~guppyft.code.toy_k2.primitives`.
"""

from typing import no_type_check

from guppylang import guppy
from guppylang.std.lang import owned
from guppylang_internals.decorator import custom_type, hugr_op

from guppyft.code._logical import _logical_op
from guppyft.extensions import toy_k2_ops, toy_k2_types

_OPS_EXTN = toy_k2_ops()


@custom_type(toy_k2_types.toy_k2_qubit_measurement(), copyable=True, droppable=True)
class QubitMeasurement:
    """Measurement of a logical qubit."""

    @hugr_op(_logical_op("decode_qubit_measurement", _OPS_EXTN))
    @no_type_check
    def decode(self: "QubitMeasurement") -> bool:
        """Decode the logical qubit measurement."""


@custom_type(toy_k2_types.toy_k2_block_measurement(), copyable=True, droppable=True)
class BlockMeasurement:
    """Measurement of both qubits in a logical block."""

    @hugr_op(_logical_op("decode_block_measurement", _OPS_EXTN))
    @no_type_check
    def decode(self: "BlockMeasurement") -> tuple[bool, bool]:
        """Decode the logical block measurement."""


@custom_type(toy_k2_types.toy_k2_block(), copyable=False, droppable=False)
class Block:
    """A ToyK2 logical block."""

    @hugr_op(_logical_op("prep_zero_ft", _OPS_EXTN))
    @no_type_check
    def __new__() -> "Block":
        r"""Fault-tolerant preparation of a logical :math:`|00\\rangle` state."""

    @guppy
    @no_type_check
    def free(self: "Block" @ owned) -> None:
        """Free the block."""
        free(self)

    @guppy
    @no_type_check
    def measure_z(self: "Block", idx: int) -> QubitMeasurement:
        """Measure the chosen qubit in the Z basis.

        Args:
            idx: The index of the logical qubit to apply the measurement to (0 or 1).
        """
        return measure_z(self, idx)

    @guppy
    @no_type_check
    def measure_z_all(self: "Block" @ owned) -> BlockMeasurement:
        """Measure both qubits of the block in the Z basis.

        This operation destroys the logical block.
        """
        return measure_z_all(self)

    @guppy
    @no_type_check
    def qed_cycle(self: "Block") -> None:
        """Performs an error detection cycle on the block.

        This consists of a syndrome extraction followed by discarding of the
        shot if the syndrome is not trivial.
        """
        qed_cycle(self)

    @guppy
    @no_type_check
    def x(self: "Block", idx: int) -> None:
        """Logical X gate to the chosen logical qubit.

        Args:
            idx: The index of the logical qubit to apply the gate to (0 or 1).
        """
        x(self, idx)

    @guppy
    @no_type_check
    def z(self: "Block", idx: int) -> None:
        """Logical Z gate to the chosen logical qubit.

        Args:
            idx: The index of the logical qubit to apply the gate to (0 or 1).
        """
        z(self, idx)

    @guppy
    @no_type_check
    def h_all(self: "Block") -> None:
        """Logical Hadamard gate on both logical qubits."""
        h_all(self)

    @guppy
    @no_type_check
    def cx_intra(self: "Block", target: int) -> None:
        """Logical CX within the block, targeting the specified logical qubit.

        Args:
            target: The index of the logical qubit that acts as target (0 or 1).
                The other logical qubit acts as control.
        """
        cx_intra(self, target)

    @guppy
    @no_type_check
    def swap_intra(self: "Block") -> None:
        """Logical SWAP within the block, swapping the two logical qubits."""
        swap_intra(self)


@custom_type(toy_k2_types.toy_k2_dynamic_qubit(), copyable=False, droppable=False)
class Qubit:
    """A dynamic ToyK2 logical qubit."""

    @hugr_op(_logical_op("alloc_dynq", _OPS_EXTN))
    @no_type_check
    def __new__() -> "Qubit":
        r"""Dynamic allocation of a logical qubit in the :math:`|0\\rangle` state."""

    @guppy
    @no_type_check
    def free(self: "Qubit" @ owned) -> None:
        """Free the dynamic qubit."""
        free_dynq(self)

    @guppy
    @no_type_check
    def x(self: "Qubit") -> None:
        """Apply a logical X gate to the dynamic qubit."""
        x_dynq(self)

    @guppy
    @no_type_check
    def z(self: "Qubit") -> None:
        """Apply a logical Z gate to the dynamic qubit."""
        z_dynq(self)

    @guppy
    @no_type_check
    def h(self: "Qubit") -> None:
        """Apply a logical Hadamard gate to the dynamic qubit."""
        h_dynq(self)

    @guppy
    @no_type_check
    def s(self: "Qubit") -> None:
        """Apply a logical S gate to the dynamic qubit."""
        s_dynq(self)

    @guppy
    @no_type_check
    def sdg(self: "Qubit") -> None:
        """Apply a logical Sdg gate to the dynamic qubit."""
        sdg_dynq(self)

    @guppy
    @no_type_check
    def t(self: "Qubit") -> None:
        """Apply a logical T gate to the dynamic qubit."""
        t_dynq(self)

    @guppy
    @no_type_check
    def tdg(self: "Qubit") -> None:
        """Apply a logical Tdg gate to the dynamic qubit."""
        tdg_dynq(self)

    @guppy
    @no_type_check
    def measure_z(self: "Qubit") -> QubitMeasurement:
        """Measure the dynamic qubit in the Z basis."""
        return measure_z_dynq(self)


@custom_type(toy_k2_types.toy_k2_borrowed_block(), copyable=False, droppable=False)
class BorrowedBlock:
    """A borrowed ToyK2 logical block."""

    @guppy
    @no_type_check
    def borrow_more(self: "BorrowedBlock", idx: int) -> Qubit:
        """Extract a logical qubit from the specified index."""
        return borrow_more(self, idx)

    @guppy
    @no_type_check
    def restore_some(self: "BorrowedBlock", qubit: Qubit @ owned) -> None:
        """Restore a logical qubits to its original block."""
        restore_some(self, qubit)


@hugr_op(_logical_op("free", _OPS_EXTN))
@no_type_check
def free(blk: Block @ owned) -> None:
    """Free a block."""


@hugr_op(_logical_op("measure_z", _OPS_EXTN))
@no_type_check
def measure_z(blk: Block, idx: int) -> QubitMeasurement:
    """Measure the chosen qubit in the Z basis."""


@hugr_op(_logical_op("measure_z_all", _OPS_EXTN))
@no_type_check
def measure_z_all(blk: Block @ owned) -> BlockMeasurement:
    """Measure both qubits of the block in the Z basis.

    This operation destroys the logical block.
    """


@hugr_op(_logical_op("qed_cycle", _OPS_EXTN))
@no_type_check
def qed_cycle(blk: Block) -> None:
    """Performs an error detection cycle on the block.

    This consists of a syndrome extraction followed by discarding of the
    shot if the syndrome is not trivial.
    """


@hugr_op(_logical_op("x", _OPS_EXTN))
@no_type_check
def x(blk: Block, idx: int) -> None:
    """Logical X gate to the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """


@hugr_op(_logical_op("z", _OPS_EXTN))
@no_type_check
def z(blk: Block, idx: int) -> None:
    """Logical Z gate to the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """


@hugr_op(_logical_op("h_all", _OPS_EXTN))
@no_type_check
def h_all(blk: Block) -> None:
    """Logical Hadamard gate on both logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """


@hugr_op(_logical_op("cx_intra", _OPS_EXTN))
@no_type_check
def cx_intra(blk: Block, target: int) -> None:
    """Logical CX within the block, targeting the specified logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        target: The index of the logical qubit that acts as target (0 or 1).
            The other logical qubit acts as control.
    """


@hugr_op(_logical_op("cx_transversal", _OPS_EXTN))
@no_type_check
def cx_transversal(control: Block, target: Block) -> None:
    """Transversal logical CX, namely, two parallel CX gates between the blocks.

    Args:
        control: The logical block that acts as control.
        target: The logical block that acts as target.
    """


@hugr_op(_logical_op("swap_intra", _OPS_EXTN))
@no_type_check
def swap_intra(blk: Block) -> None:
    """Logical SWAP within the block, swapping the two logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """


@hugr_op(_logical_op("prep_y_states_non_ft", _OPS_EXTN))
@no_type_check
def prep_y_states_non_ft() -> Block:
    r"""Non fault-tolerant preparation of a logical :math:`|Y\rangle|Y\rangle` state.

    The architecture uses these states to inject :math:`S` and :math:`S^\dagger` gates.
    """


@hugr_op(_logical_op("prep_t_states_non_ft", _OPS_EXTN))
@no_type_check
def prep_t_states_non_ft() -> Block:
    r"""Non fault-tolerant preparation of a logical :math:`T|+\rangle T|+\rangle` state.

    The architecture uses these states to inject :math:`T` and :math:`T^\dagger` gates.
    """


@hugr_op(_logical_op("free_dynq", _OPS_EXTN))
@no_type_check
def free_dynq(q: Qubit @ owned) -> None:
    """Free a dynamic logical qubit."""


@hugr_op(_logical_op("x_dynq", _OPS_EXTN))
@no_type_check
def x_dynq(q: Qubit) -> None:
    """Apply an X gate to a dynamic logical qubit."""


@hugr_op(_logical_op("z_dynq", _OPS_EXTN))
@no_type_check
def z_dynq(q: Qubit) -> None:
    """Apply a Z gate to a dynamic logical qubit."""


@hugr_op(_logical_op("h_dynq", _OPS_EXTN))
@no_type_check
def h_dynq(q: Qubit) -> None:
    """Apply a Hadamard gate to a dynamic logical qubit."""


@hugr_op(_logical_op("s_dynq", _OPS_EXTN))
@no_type_check
def s_dynq(q: Qubit) -> None:
    """Apply an S gate to a dynamic logical qubit."""


@hugr_op(_logical_op("sdg_dynq", _OPS_EXTN))
@no_type_check
def sdg_dynq(q: Qubit) -> None:
    """Apply an Sdg gate to a dynamic logical qubit."""


@hugr_op(_logical_op("t_dynq", _OPS_EXTN))
@no_type_check
def t_dynq(q: Qubit) -> None:
    """Apply an T gate to a dynamic logical qubit."""


@hugr_op(_logical_op("tdg_dynq", _OPS_EXTN))
@no_type_check
def tdg_dynq(q: Qubit) -> None:
    """Apply a Tdg gate to a dynamic logical qubit."""


@hugr_op(_logical_op("cx_dynq", _OPS_EXTN))
@no_type_check
def cx_dynq(control: Qubit, target: Qubit) -> None:
    """Apply a CX gate to dynamic logical qubits."""


@hugr_op(_logical_op("measure_z_dynq", _OPS_EXTN))
@no_type_check
def measure_z_dynq(q: Qubit) -> QubitMeasurement:
    """Measure a dynamic logical qubit in the Z basis."""


@hugr_op(_logical_op("borrow", _OPS_EXTN))
@no_type_check
def borrow(block: Block @ owned, idx: int) -> (BorrowedBlock, Qubit):
    """Extract a logical qubit from the specified index in the block."""


@hugr_op(_logical_op("borrow_more", _OPS_EXTN))
@no_type_check
def borrow_more(block: BorrowedBlock, idx: int) -> Qubit:
    """Extract an additional logical qubit from the block, from the specified index."""


@hugr_op(_logical_op("restore_some", _OPS_EXTN))
@no_type_check
def restore_some(block: BorrowedBlock, q: Qubit @ owned) -> None:
    """Restore a previously borrowed logical qubit to its block."""


@hugr_op(_logical_op("restore", _OPS_EXTN))
@no_type_check
def restore(block: BorrowedBlock @ owned, q: Qubit @ owned) -> Block:
    """Restore a the last of the borrowed logical qubits back to its block."""


@guppy
@no_type_check
def cx_inter(ctrl_block: Block, ctrl_idx: int, tgt_block: Block, tgt_idx: int) -> None:
    """Logical CX between two blocks, targeting the specified logical qubits.

    Args:
        ctrl_block: The logical block that acts as control.
        ctrl_idx: The index of the logical qubit in the control block (0 or 1).
        tgt_block: The logical block that acts as target.
        tgt_idx: The index of the logical qubit in the target block (0 or 1).
    """
    if ctrl_idx == tgt_idx:
        swap_intra(ctrl_block)

    cx_transversal(ctrl_block, tgt_block)
    cx_intra(tgt_block, tgt_idx)
    cx_transversal(ctrl_block, tgt_block)
    cx_intra(tgt_block, tgt_idx)

    if ctrl_idx == tgt_idx:
        swap_intra(ctrl_block)


@guppy
@no_type_check
def h(block: Block, idx: int) -> None:
    """Logical Hadamard gate on the specified logical qubit.

    Args:
        block: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    # Prepare an ancilla `|0+>` state, with the `|+>` on the index where we want
    # to apply the Hadamard.
    ancilla = Block()  # |00>
    h_all(ancilla)  # |++>
    # Project the other ancilla logical qubit to |0>
    if measure_z(ancilla, 1 - idx).decode():
        x(ancilla, idx)

    # Use the ancilla state to introduce a Hadamard on the chosen index.
    # This approach follows Fig 8A from https://arxiv.org/abs/2403.16054
    # In the case where ancilla is |0>, the CX gates are cancelled and there is
    # no effect on the logical qubit at that index.
    # In the case where the ancilla is |+>, a H is applied on the block,
    # up to a Z correction if the measurement outcome is 0 and X if it is 1.
    cx_transversal(ancilla, block)
    h_all(ancilla)
    cx_transversal(block, ancilla)
    m0, m1 = measure_z_all(ancilla).decode()
    m = m0 if idx == 0 else m1

    if m:
        x(block, idx)
    else:
        z(block, idx)


@guppy
@no_type_check
def s_all(block: Block) -> None:
    """Logical S or Sdg gate on both logical qubits.

    Args:
        block: The logical block to apply the gate to.
    """
    y_states = prep_y_states_non_ft()

    cx_transversal(block, y_states)
    m0, m1 = measure_z_all(y_states).decode()

    if m0:
        z(block, 0)
    if m1:
        z(block, 1)


@guppy
@no_type_check
def s(block: Block, idx: int) -> None:
    """Logical S gate on the specified logical qubit.

    Args:
        block: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    y_states = prep_y_states_non_ft()

    cx_inter(block, idx, y_states, idx)
    m0, m1 = measure_z_all(y_states).decode()
    m = m0 if idx == 0 else m1

    if m:
        z(block, idx)


@guppy
@no_type_check
def sdg(block: Block, idx: int) -> None:
    """Logical Sdg gate on the specified logical qubit.

    Args:
        block: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    x(block, idx)
    s(block, idx)
    x(block, idx)


@guppy
@no_type_check
def t_all(block: Block) -> None:
    """Logical T or Tdg gate on both logical qubits.

    Args:
        block: The logical block to apply the gate to.
    """
    t_states = prep_t_states_non_ft()

    cx_transversal(block, t_states)
    m0, m1 = measure_z_all(t_states).decode()

    if m0 and m1:
        s_all(block)
    elif m0:
        s(block, 0)
    elif m1:
        s(block, 1)


@guppy
@no_type_check
def t(block: Block, idx: int) -> None:
    """Logical T gate on the specified logical qubit.

    Args:
        block: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    t_states = prep_t_states_non_ft()

    cx_inter(block, idx, t_states, idx)
    m0, m1 = measure_z_all(t_states).decode()
    m = m0 if idx == 0 else m1

    if m:
        s(block, idx)


@guppy
@no_type_check
def tdg(block: Block, idx: int) -> None:
    """Logical Tdg gate on the specified logical qubit.

    Args:
        block: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    x(block, idx)
    t(block, idx)
    x(block, idx)
