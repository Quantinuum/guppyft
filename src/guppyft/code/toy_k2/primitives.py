"""Logical primitives for a CSS [[4,2,2]] code."""

from typing import no_type_check

from guppylang import guppy
from guppylang.std import quantum as phys
from guppylang.std.builtins import array, owned
from guppylang.std.collections import Queue, empty_queue
from guppylang.std.mem import mem_swap

from guppyft.code._state_factory import PreBlock
from guppyft.code.util import LogicalBlock
from guppyft.code_def import StabilizerCode

CODE_DEF = StabilizerCode.from_python_strings(
    num_physical_qubits=4,
    num_logical_qubits=2,
    distance=2,
    generators=["XXXX", "ZZZZ"],
    x_logicals=["IXIX", "IIXX"],
    z_logicals=["ZZII", "ZIZI"],
)


@guppy
@no_type_check
def x(blk: LogicalBlock[4], idx: int) -> None:
    """Logical X gate on the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    if idx != 0 and idx != 1:
        exit("Invalid logical qubit index. Must be 0 or 1.")
    phys.x(blk.data_qs[3])
    phys.x(blk.data_qs[idx + 1])


@guppy
@no_type_check
def z(blk: LogicalBlock[4], idx: int) -> None:
    """Logical Z gate on the chosen logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        idx: The index of the logical qubit to apply the gate to (0 or 1).
    """
    if idx != 0 and idx != 1:
        exit("Invalid logical qubit index. Must be 0 or 1.")
    phys.z(blk.data_qs[0])
    phys.z(blk.data_qs[idx + 1])


@guppy
@no_type_check
def h_all(blk: LogicalBlock[4]) -> None:
    """Logical Hadamard gate on both logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """
    for i in range(len(blk.data_qs)):
        phys.h(blk.data_qs[i])
    mem_swap(blk.data_qs[1], blk.data_qs[2])


@guppy
@no_type_check
def cx_intra(blk: LogicalBlock[4], target: int) -> None:
    """Logical CX within the block, targeting the specified logical qubit.

    Args:
        blk: The logical block to apply the gate to.
        target: The index of the logical qubit that acts as target (0 or 1).
            The other logical qubit acts as control.
    """
    if target != 0 and target != 1:
        exit("Invalid logical qubit index. Must be 0 or 1.")

    if target == 1:
        mem_swap(blk.data_qs[0], blk.data_qs[1])
    else:
        mem_swap(blk.data_qs[0], blk.data_qs[2])


@guppy
@no_type_check
def cx_transversal(control: LogicalBlock[4], target: LogicalBlock[4]) -> None:
    """Transversal logical CX, namely, two parallel CX gates between the blocks.

    Args:
        control: The logical block that acts as control.
        target: The logical block that acts as target.
    """
    for i in range(len(control.data_qs)):
        phys.cx(control.data_qs[i], target.data_qs[i])


@guppy
@no_type_check
def swap_intra(blk: LogicalBlock[4]) -> None:
    """Logical SWAP within the block, swapping the two logical qubits.

    Args:
        blk: The logical block to apply the gate to.
    """
    mem_swap(blk.data_qs[1], blk.data_qs[2])


@guppy
@no_type_check
def prep_zero_ft() -> PreBlock[4, 1]:
    """Fault-tolerant preparation of a logical :math:`|00\\rangle` state.

    The logical block is wrapped in a `PreBlock`, which contains the flag
    measurement outcomes. Use `force_check()` to check if preparation was
    successful, retrieving the logical block.
    """
    # Create an array of physical qubits
    phys_qs = array(phys.qubit() for _ in range(4))

    # Implement a physical GHZ state, which corresponds to logical |00> state.
    phys.h(phys_qs[0])
    phys.cx(phys_qs[0], phys_qs[1])
    phys.cx(phys_qs[0], phys_qs[2])
    phys.cx(phys_qs[0], phys_qs[3])

    # Flag using an ancilla qubit
    ancilla = phys.qubit()
    phys.cx(phys_qs[0], ancilla)
    phys.cx(phys_qs[3], ancilla)
    flag_meas = phys.measure(ancilla)

    return PreBlock(LogicalBlock(phys_qs), array(flag_meas))


@guppy
@no_type_check
def _encode_state_non_ft(
    q0: phys.qubit @ owned, q1: phys.qubit @ owned
) -> LogicalBlock[4]:
    """Non fault-tolerant encoding of a physical state into a logical block.

    The logical state returned corresponds to the state of the physical
    qubits provided as input.
    """
    # Create an array of physical qubits, including the two input qubits
    phys_qs = array(q0, phys.qubit(), phys.qubit(), q1)

    # Encode the physical qubit into the logical block
    phys.h(phys_qs[1])
    phys.cx(phys_qs[1], phys_qs[0])
    phys.cx(phys_qs[3], phys_qs[2])
    phys.cx(phys_qs[0], phys_qs[2])
    phys.cx(phys_qs[1], phys_qs[3])

    return LogicalBlock(phys_qs)


@guppy
@no_type_check
def prep_y_states_non_ft() -> LogicalBlock[4]:
    r"""Non fault-tolerant preparation of a logical :math:`|Y\rangle|Y\rangle` state.

    The :math:`|Y\rangle` state is the +1 eigenvector of the Pauli Y operator,
    equivalently, :math:`|Y\rangle = S|+\rangle`.
    The architecture uses these states to inject :math:`S` and :math:`S^\dagger` gates.
    """
    # Prepare two physical |Y> states
    q0, q1 = phys.qubit(), phys.qubit()
    phys.h(q0)
    phys.h(q1)
    phys.s(q0)
    phys.s(q1)

    # Encode them into a logical block
    return _encode_state_non_ft(q0, q1)


@guppy
@no_type_check
def prep_t_states_non_ft() -> LogicalBlock[4]:
    r"""Non fault-tolerant preparation of a logical :math:`T|+\rangle T|+\rangle` state.

    The architecture uses these states to inject :math:`T` and :math:`T^\dagger` gates.
    """
    # Prepare two physical T|+> states
    q0, q1 = phys.qubit(), phys.qubit()
    phys.h(q0)
    phys.h(q1)
    phys.t(q0)
    phys.t(q1)

    # Encode them into a logical block
    return _encode_state_non_ft(q0, q1)


@guppy
@no_type_check
def measure_z_all(blk: LogicalBlock[4] @ owned) -> array[bool, 2]:
    """Measure both qubits of the block in the Z basis.

    This operation destroys the logical block.
    """
    # TODO: Move this to a decode function to defer measurements
    meas = phys.collect_measurements(phys.measure_array(blk.data_qs))

    z_stab = meas[0] ^ meas[1] ^ meas[2] ^ meas[3]
    q0_outcome = meas[0] ^ meas[1]
    q1_outcome = meas[0] ^ meas[2]

    if z_stab:
        exit("Detected an X error during measurement of a logical block.")

    return array(q0_outcome, q1_outcome)


@guppy
@no_type_check
def measure_z(blk: LogicalBlock[4], idx: int) -> bool:
    """Measure the chosen qubit in the Z basis."""
    if idx != 0 and idx != 1:
        exit("Invalid logical qubit index. Must be 0 or 1.")

    # The logical Z observable is measured twice to detect measurement errors.
    # If the two outcomes do not agree, an error is detected.
    obs_measurements: Queue[phys.Measurement, 2] = empty_queue()  # type: ignore[type-arg,valid-type]
    # If the flag measurements return `True`, an error is detected.
    flag_measurements: Queue[phys.Measurement, 2] = empty_queue()  # type: ignore[type-arg,valid-type]

    for _ in range(2):
        # Prepare the ancilla in a Bell state
        obs_ancilla = phys.qubit()
        flag_ancilla = phys.qubit()
        phys.h(flag_ancilla)
        phys.cx(flag_ancilla, obs_ancilla)

        # Apply the CX to entangle with the block
        phys.cx(blk.data_qs[0], obs_ancilla)
        phys.cx(blk.data_qs[idx + 1], flag_ancilla)

        # Apply a Bell measurement on the ancillas
        phys.cx(flag_ancilla, obs_ancilla)
        phys.h(flag_ancilla)
        obs_meas = phys.measure(obs_ancilla)
        flag_meas = phys.measure(flag_ancilla)

        # Add to stacks to defer `read`
        obs_measurements.push(obs_meas)
        flag_measurements.push(flag_meas)

    # TODO: For now, read and return bool, but consider using a
    # protocol later on, so that it has a decode that can be replaced.

    for m in flag_measurements:
        if m.read():
            exit(
                "Detected an error during measurement of a logical qubit."
                " Flag measurement was non-trivial."
            )

    obs_out_0 = obs_measurements.pop().read()
    obs_out_1 = obs_measurements.pop().read()

    if obs_out_0 != obs_out_1:
        exit(
            "Detected an error during non-destructive measurement of a logical qubit."
            " Incompatible measurement results."
        )

    return obs_out_0


@guppy
@no_type_check
def _syndrome_extraction(
    blk: LogicalBlock[4],
) -> tuple[phys.Measurement, phys.Measurement]:
    """Extracts the syndrome of the block.

    Returns:
        Two stabilizer measurements, corresponding to :math:`XXXX`
        and :math:`ZZZZ`, in that order.
    """
    x_stab_ancilla = phys.qubit()
    z_stab_ancilla = phys.qubit()
    phys.h(x_stab_ancilla)

    phys.cx(x_stab_ancilla, blk.data_qs[0])
    phys.cx(blk.data_qs[0], z_stab_ancilla)
    phys.cx(blk.data_qs[1], z_stab_ancilla)
    phys.cx(x_stab_ancilla, blk.data_qs[1])
    phys.cx(x_stab_ancilla, blk.data_qs[2])
    phys.cx(blk.data_qs[2], z_stab_ancilla)
    phys.cx(blk.data_qs[3], z_stab_ancilla)
    phys.cx(x_stab_ancilla, blk.data_qs[3])

    phys.h(x_stab_ancilla)
    x_stab_meas = phys.measure(x_stab_ancilla)
    z_stab_meas = phys.measure(z_stab_ancilla)

    return x_stab_meas, z_stab_meas


@guppy
@no_type_check
def qed_cycle(blk: LogicalBlock[4]) -> None:
    """Performs an error detection cycle on the block.

    This consists of a syndrome extraction followed by discarding of the
    shot if the syndrome is not trivial.
    """
    x_stab_meas, z_stab_meas = _syndrome_extraction(blk)

    if x_stab_meas.read():
        exit("A QED cycle detected a Z error.")
    if z_stab_meas.read():
        exit("A QED cycle detected an X error.")
