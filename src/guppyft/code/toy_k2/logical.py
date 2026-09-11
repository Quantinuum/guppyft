from collections.abc import Callable
from typing import no_type_check

from guppylang import guppy
from guppylang.std.lang import owned
from guppylang_internals.decorator import custom_type, hugr_op
from guppylang_internals.tys.common import ToHugrContext
from guppylang_internals.tys.subst import Inst
from hugr import tys as ht
from hugr.ops import DataflowOp, ExtOp

from guppyft.extensions import toy_k2_ops, toy_k2_types

_OPS_EXTN = toy_k2_ops()


def toy_k2_op(
    op_name: str,
) -> Callable[[ht.FunctionType, Inst, ToHugrContext], DataflowOp]:
    def op(ty: ht.FunctionType, inst: Inst, ctx: ToHugrContext) -> DataflowOp:
        return ExtOp(_OPS_EXTN.get_op(op_name), ty, [arg.to_hugr(ctx) for arg in inst])

    return op


@custom_type(toy_k2_types.toy_k2_qubit_measurement(), copyable=True, droppable=True)
class QubitMeasurement:
    @hugr_op(toy_k2_op("decode_qubit_measurement"))
    @no_type_check
    def decode(self: "QubitMeasurement") -> bool:
        """Decode the logical qubit measurement."""


@custom_type(toy_k2_types.toy_k2_block_measurement(), copyable=True, droppable=True)
class BlockMeasurement:
    @hugr_op(toy_k2_op("decode_block_measurement"))
    @no_type_check
    def decode(self: "BlockMeasurement") -> tuple[bool, bool]:
        """Decode the logical block measurement."""


@custom_type(toy_k2_types.toy_k2_block(), copyable=False, droppable=False)
class Block:
    @hugr_op(toy_k2_op("prep_zero_ft"))
    @no_type_check
    def __new__() -> "Block":
        """Fault-tolerant preparation of a logical :math:`|00\\rangle` state."""

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


@hugr_op(toy_k2_op("free"))
@no_type_check
def free(blk: "Block" @ owned) -> None:
    """Free a block."""


@hugr_op(toy_k2_op("measure_z"))
@no_type_check
def measure_z(blk: "Block", idx: int) -> QubitMeasurement:
    """Measure the chosen qubit in the Z basis."""


@hugr_op(toy_k2_op("measure_z_all"))
@no_type_check
def measure_z_all(blk: "Block" @ owned) -> BlockMeasurement:
    """Measure both qubits of the block in the Z basis.

    This operation destroys the logical block.
    """


@hugr_op(toy_k2_op("qed_cycle"))
@no_type_check
def qed_cycle(blk: "Block") -> None:
    """Performs an error detection cycle on the block.

    This consists of a syndrome extraction followed by discarding of the
    shot if the syndrome is not trivial.
    """


@hugr_op(toy_k2_op("x"))
@no_type_check
def x(blk: "Block", idx: int) -> None:
    """Logical X gate to the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """


@hugr_op(toy_k2_op("z"))
@no_type_check
def z(blk: "Block", idx: int) -> None:
    """Logical Z gate to the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """


@hugr_op(toy_k2_op("h_all"))
@no_type_check
def h_all(blk: "Block") -> None:
    """Logical Hadamard gate on both logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """


@hugr_op(toy_k2_op("cx_intra"))
@no_type_check
def cx_intra(blk: "Block", target: int) -> None:
    """Logical CX within the block, targeting the specified logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        target: The index of the logical qubit that acts as target (0 or 1).
            The other logical qubit acts as control.
    """


@hugr_op(toy_k2_op("cx_transversal"))
@no_type_check
def cx_transversal(control: "Block", target: "Block") -> None:
    """Transversal logical CX, namely, two parallel CX gates between the blocks.

    Args:
        control: The logical block that acts as control.
        target: The logical block that acts as target.
    """


@hugr_op(toy_k2_op("swap_intra"))
@no_type_check
def swap_intra(blk: "Block") -> None:
    """Logical SWAP within the block, swapping the two logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """


@hugr_op(toy_k2_op("prep_y_states_non_ft"))
@no_type_check
def prep_y_states_non_ft() -> "Block":
    r"""Non fault-tolerant preparation of a logical :math:`|Y\rangle|Y\rangle` state.

    The architecture uses these states to inject :math:`S` and :math:`S^\dagger` gates.
    """


@hugr_op(toy_k2_op("prep_t_states_non_ft"))
@no_type_check
def prep_t_states_non_ft() -> "Block":
    r"""Non fault-tolerant preparation of a logical :math:`T|+\rangle T|+\rangle` state.

    The architecture uses these states to inject :math:`T` and :math:`T^\dagger` gates.
    """


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
