"""Steane code extension."""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import ExtType

from ._util import load_extension


class SteaneTypesExtension:
    """Extension providing the Steane qubit."""

    def __call__(self) -> Extension:
        """Returns the Steane types extension"""
        return load_extension("guppyft.steane.types")

    @functools.cached_property
    def steane_qubit_def(self) -> TypeDef:
        """A Steane logical qubit.

        This is the generic type definition. For the instantiated type, see
        `steane_qubit`.
        """
        return self().get_type("qubit")

    def steane_qubit(self) -> ExtType:
        """A Steane logical qubit."""
        return self.steane_qubit_def.instantiate([])

    @functools.cached_property
    def steane_measurement_def(self) -> TypeDef:
        """A Steane logical measurement type.

        This is the generic type definition. For the instantiated type, see
        `steane_measurement`.
        """
        return self().get_type("measurement")

    def steane_measurement(self) -> ExtType:
        """A Steane logical measurement."""
        return self.steane_measurement_def.instantiate([])


class SteaneOpsExtension:
    """Extension providing the Steane logical operations."""

    def __call__(self) -> Extension:
        """Returns the Steane ops extension"""
        return load_extension("guppyft.steane.ops")

    @functools.cached_property
    def prep_zero_def(self) -> OpDef:
        """Prepare a logical qubit in the all-zero state.

        This is the generic operation definition. For the instantiated operation, see
        `prep_zero`."""
        return self().get_op("prep_zero")

    def prep_zero(self) -> ExtOp:
        """Allocate a block in the all-zero state."""
        return self.prep_zero_def.instantiate([])

    @functools.cached_property
    def free_def(self) -> OpDef:
        """Free a logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `free`."""
        return self().get_op("free")

    def free(self) -> ExtOp:
        """Free a block."""
        return self.free_def.instantiate([])

    @functools.cached_property
    def measure_z_def(self) -> OpDef:
        """Destructive measurement of a logical qubit in the Z basis.

        This is the generic operation definition. For the instantiated operation, see
        `measure_z`."""
        return self().get_op("measure_z")

    def measure_z(self) -> ExtOp:
        """Destructive measurement of a logical qubit in the Z basis."""
        return self.measure_z_def.instantiate([])

    @functools.cached_property
    def decode_def(self) -> OpDef:
        """Decode a measurement of a Steane logical qubit.

        This is the generic operation definition. For the instantiated operation, see
        `decode`."""
        return self().get_op("decode")

    def decode(self) -> ExtOp:
        """Decode a measurement of a Steane logical qubit."""
        return self.decode_def.instantiate([])

    @functools.cached_property
    def x_def(self) -> OpDef:
        """Apply an X gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `x`."""
        return self().get_op("x")

    def x(self) -> ExtOp:
        """Apply an X gate to one qubit."""
        return self.x_def.instantiate([])

    @functools.cached_property
    def z_def(self) -> OpDef:
        """Apply a Z gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `z`."""
        return self().get_op("z")

    def z(self) -> ExtOp:
        """Apply a Z gate to one qubit."""
        return self.z_def.instantiate([])

    @functools.cached_property
    def h_def(self) -> OpDef:
        """Apply an H gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `h`."""
        return self().get_op("h")

    def h(self) -> ExtOp:
        """Apply an H gate to one qubit."""
        return self.h_def.instantiate([])

    @functools.cached_property
    def s_def(self) -> OpDef:
        """Apply an S gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `s`."""
        return self().get_op("s")

    def s(self) -> ExtOp:
        """Apply an S gate to one qubit."""
        return self.s_def.instantiate([])

    @functools.cached_property
    def sdg_def(self) -> OpDef:
        """Apply an Sdg gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `sdg`."""
        return self().get_op("sdg")

    def sdg(self) -> ExtOp:
        """Apply an Sdg gate to one qubit."""
        return self.sdg_def.instantiate([])

    @functools.cached_property
    def prep_magic_for_t_like_def(self) -> OpDef:
        """Prepare a magic state that can be used to produce T-like states (T and Tdg).

        This is the generic operation definition. For the instantiated operation, see
        `prep_magic_for_t_like`."""
        return self().get_op("prep_magic_for_t_like")

    def prep_magic_for_t_like(self) -> ExtOp:
        """
        Prepare a magic state that can be used to produce T-like states (T and Tdg).
        """
        return self.prep_magic_for_t_like_def.instantiate([])

    @functools.cached_property
    def inject_magic_for_t_def(self) -> OpDef:
        """Perform a T gate by injecting a magic state.

        This is the generic operation definition. For the instantiated operation, see
        `inject_magic_for_t`."""
        return self().get_op("inject_magic_for_t")

    def inject_magic_for_t(self) -> ExtOp:
        """Perform a T gate by injecting a magic state."""
        return self.inject_magic_for_t_def.instantiate([])

    @functools.cached_property
    def inject_magic_for_tdg_def(self) -> OpDef:
        """Perform a Tdg gate by injecting a magic state.

        This is the generic operation definition. For the instantiated operation, see
        `inject_magic_for_tdg`."""
        return self().get_op("inject_magic_for_tdg")

    def inject_magic_for_tdg(self) -> ExtOp:
        """Perform a Tdg gate by injecting a magic state."""
        return self.inject_magic_for_tdg_def.instantiate([])

    @functools.cached_property
    def cx_def(self) -> OpDef:
        """Apply a CX gate to two qubits.

        This is the generic operation definition. For the instantiated operation, see
        `cx`."""
        return self().get_op("cx")

    def cx(self) -> ExtOp:
        """Apply a CX gate to two qubits."""
        return self.cx_def.instantiate([])

    @functools.cached_property
    def swap_def(self) -> OpDef:
        """Apply a SWAP gate to two qubits.

        This is the generic operation definition. For the instantiated operation, see
        `swap`."""
        return self().get_op("swap")

    def swap(self) -> ExtOp:
        """Apply a SWAP gate to two qubits."""
        return self.swap_def.instantiate([])
