"""ToyK2 code extension."""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import ExtType

from ._util import load_extension


class ToyK2TypesExtension:
    """Extension providing the ToyK2 types."""

    def __call__(self) -> Extension:
        """Returns the ToyK2 types extension"""
        return load_extension("guppyft.toy_k2.types")

    @functools.cached_property
    def toy_k2_block_def(self) -> TypeDef:
        """A ToyK2 logical block.

        This is the generic type definition. For the instantiated type, see
        `toy_k2_block`.
        """
        return self().get_type("block")

    def toy_k2_block(self) -> ExtType:
        """A ToyK2 logical block."""
        return self.toy_k2_block_def.instantiate([])

    @functools.cached_property
    def toy_k2_block_measurement_def(self) -> TypeDef:
        """A ToyK2 logical block measurement type.

        This is the generic type definition. For the instantiated type, see
        `toy_k2_block_measurement`.
        """
        return self().get_type("block_measurement")

    def toy_k2_block_measurement(self) -> ExtType:
        """A ToyK2 logical block measurement."""
        return self.toy_k2_block_measurement_def.instantiate([])

    @functools.cached_property
    def toy_k2_qubit_measurement_def(self) -> TypeDef:
        """A ToyK2 logical qubit measurement type.

        This is the generic type definition. For the instantiated type, see
        `toy_k2_qubit_measurement`.
        """
        return self().get_type("qubit_measurement")

    def toy_k2_qubit_measurement(self) -> ExtType:
        """A ToyK2 logical qubit measurement."""
        return self.toy_k2_qubit_measurement_def.instantiate([])


class ToyK2OpsExtension:
    """Extension providing the ToyK2 logical operations."""

    def __call__(self) -> Extension:
        """Returns the ToyK2 ops extension"""
        return load_extension("guppyft.toy_k2.ops", ["guppyft.std.types"])

    @functools.cached_property
    def x_def(self) -> OpDef:
        """Logical X gate on the chosen logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `x`."""
        return self().get_op("x")

    def x(self) -> ExtOp:
        """Logical X gate on the chosen logical qubit."""
        return self.x_def.instantiate([])

    @functools.cached_property
    def z_def(self) -> OpDef:
        """Logical Z gate on the chosen logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `z`."""
        return self().get_op("z")

    def z(self) -> ExtOp:
        """Logical Z gate on the chosen logical qubit."""
        return self.z_def.instantiate([])

    @functools.cached_property
    def h_all_def(self) -> OpDef:
        """Logical Hadamard gate on both logical qubits.

        This is the generic operation definition. For the instantiated operation, see
        `h_all`."""
        return self().get_op("h_all")

    def h_all(self) -> ExtOp:
        """Logical Hadamard gate on both logical qubits."""
        return self.h_all_def.instantiate([])

    @functools.cached_property
    def cx_intra_def(self) -> OpDef:
        """Logical CX within the block, targeting the specified logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `cx_intra`."""
        return self().get_op("cx_intra")

    def cx_intra(self) -> ExtOp:
        """Logical CX within the block, targeting the specified logical qubit."""
        return self.cx_intra_def.instantiate([])

    @functools.cached_property
    def cx_transversal_def(self) -> OpDef:
        """Transversal logical CX, namely, two parallel CX gates between the blocks.

        This is the generic operation definition. For the instantiated operation, see
        `cx_transversal`."""
        return self().get_op("cx_transversal")

    def cx_transversal(self) -> ExtOp:
        """Transversal logical CX, namely, two parallel CX gates between the blocks."""
        return self.cx_transversal_def.instantiate([])

    @functools.cached_property
    def swap_intra_def(self) -> OpDef:
        """Logical SWAP within the block, swapping the two logical qubits.

        This is the generic operation definition. For the instantiated operation, see
        `swap_intra`."""
        return self().get_op("swap_intra")

    def swap_intra(self) -> ExtOp:
        """Logical SWAP within the block, swapping the two logical qubits."""
        return self.swap_intra_def.instantiate([])

    @functools.cached_property
    def prep_zero_ft_def(self) -> OpDef:
        """Fault-tolerant preparation of a logical :math:`|00\\rangle` state.

        This is the generic operation definition. For the instantiated operation, see
        `prep_zero_ft`."""
        return self().get_op("prep_zero_ft")

    def prep_zero_ft(self) -> ExtOp:
        """Fault-tolerant preparation of a logical :math:`|00\\rangle` state."""
        return self.prep_zero_ft_def.instantiate([])

    @functools.cached_property
    def prep_y_states_non_ft_def(self) -> OpDef:
        r"""Non fault-tolerant preparation of a logical
        :math:`|Y\rangle|Y\rangle` state.

        This is the generic operation definition. For the instantiated operation, see
        `prep_y_states_non_ft`."""
        return self().get_op("prep_y_states_non_ft")

    def prep_y_states_non_ft(self) -> ExtOp:
        r"""Non fault-tolerant preparation of a logical
        :math:`|Y\rangle|Y\rangle` state."""
        return self.prep_y_states_non_ft_def.instantiate([])

    @functools.cached_property
    def prep_t_states_non_ft_def(self) -> OpDef:
        r"""Non fault-tolerant preparation of a logical
        :math:`T|+\rangle T|+\rangle` state.

        This is the generic operation definition. For the instantiated operation, see
        `prep_t_states_non_ft`."""
        return self().get_op("prep_t_states_non_ft")

    def prep_t_states_non_ft(self) -> ExtOp:
        r"""Non fault-tolerant preparation of a logical
        :math:`T|+\rangle T|+\rangle` state."""
        return self.prep_t_states_non_ft_def.instantiate([])

    @functools.cached_property
    def measure_z_all_def(self) -> OpDef:
        """Measure both qubits of the block in the Z basis.

        This is the generic operation definition. For the instantiated operation, see
        `measure_z_all`."""
        return self().get_op("measure_z_all")

    def measure_z_all(self) -> ExtOp:
        """Measure both qubits of the block in the Z basis."""
        return self.measure_z_all_def.instantiate([])

    @functools.cached_property
    def measure_z_def(self) -> OpDef:
        """Measure the chosen qubit in the Z basis.

        This is the generic operation definition. For the instantiated operation, see
        `measure_z`."""
        return self().get_op("measure_z")

    def measure_z(self) -> ExtOp:
        """Measure the chosen qubit in the Z basis."""
        return self.measure_z_def.instantiate([])

    @functools.cached_property
    def qed_cycle_def(self) -> OpDef:
        """Performs an error detection cycle on the block.

        This is the generic operation definition. For the instantiated operation, see
        `qed_cycle`."""
        return self().get_op("qed_cycle")

    def qed_cycle(self) -> ExtOp:
        """Performs an error detection cycle on the block."""
        return self.qed_cycle_def.instantiate([])

    @functools.cached_property
    def free_def(self) -> OpDef:
        """Free a logical block.

        This is the generic operation definition. For the instantiated operation, see
        `free`."""
        return self().get_op("free")

    def free(self) -> ExtOp:
        """Free a logical block."""
        return self.free_def.instantiate([])

    @functools.cached_property
    def decode_block_measurement_def(self) -> OpDef:
        """Decode a measurement of a ToyK2 logical block.

        This is the generic operation definition. For the instantiated operation, see
        `decode_block_measurement`."""
        return self().get_op("decode_block_measurement")

    def decode_block_measurement(self) -> ExtOp:
        """Decode a measurement of a ToyK2 logical block."""
        return self.decode_block_measurement_def.instantiate([])

    @functools.cached_property
    def decode_qubit_measurement_def(self) -> OpDef:
        """Decode a measurement of a ToyK2 logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `decode_qubit_measurement`."""
        return self().get_op("decode_qubit_measurement")

    def decode_qubit_measurement(self) -> ExtOp:
        """Decode a measurement of a ToyK2 logical qubit."""
        return self.decode_qubit_measurement_def.instantiate([])
