"""Python bindings for the C4-Helix HUGR types and operations extensions."""

import functools

from hugr.ext import Extension, ExtensionRegistry, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.std.int import INT_TYPES_EXTENSION
from hugr.tys import ExtType

from ._util import load_extension, load_extension_json


class HelixTypesExtension:
    """Extension providing linear Helix blocks and T-state resources."""

    def __call__(self) -> Extension:
        """Return the Helix types extension."""
        return load_extension("guppyft.helix.types")

    @functools.cached_property
    def helix_block_def(self) -> TypeDef:
        """A Helix block containing two logical qubits, labelled 0 and 1.

        For the instantiated type, see `helix_block`.
        """
        return self().get_type("block")

    def helix_block(self) -> ExtType:
        """A Helix block containing two logical qubits, labelled 0 and 1."""
        return self.helix_block_def.instantiate([])

    @functools.cached_property
    def helix_t_state_def(self) -> TypeDef:
        """An opaque, consumable T-state resource.

        For the instantiated type, see `helix_t_state`.
        """
        return self().get_type("t_state")

    def helix_t_state(self) -> ExtType:
        """An opaque, consumable T-state resource."""
        return self.helix_t_state_def.instantiate([])


_HELIX_TYPES = HelixTypesExtension()


class HelixOpsExtension:
    """Extension providing Helix logical operations.

    Each block comprises two logical qubits, labelled 0 and 1. These indices are
    runtime HUGR inputs.
    """

    def __call__(self) -> Extension:
        """Return the Helix ops extension with its type dependencies resolved."""
        registry = ExtensionRegistry.from_extensions(
            [
                _HELIX_TYPES(),
                load_extension("guppyft.std.types"),
                INT_TYPES_EXTENSION,
            ]
        )
        return Extension.from_json(load_extension_json("guppyft.helix.ops"), registry)

    @functools.cached_property
    def alloc_plus_def(self) -> OpDef:
        """Definition of the `alloc_plus` operation.

        For the instantiated operation, see `alloc_plus`.
        """
        return self().get_op("alloc_plus")

    def alloc_plus(self) -> ExtOp:
        """Prepare the ``|++>`` state on a block."""
        return self.alloc_plus_def.instantiate([])

    @functools.cached_property
    def alloc_zero_def(self) -> OpDef:
        """Definition of the `alloc_zero` operation.

        For the instantiated operation, see `alloc_zero`.
        """
        return self().get_op("alloc_zero")

    def alloc_zero(self) -> ExtOp:
        """Prepare the all-zero state on a block."""
        return self.alloc_zero_def.instantiate([])

    @functools.cached_property
    def cx_between_blocks_def(self) -> OpDef:
        """Definition of the `cx_between_blocks` operation.

        For the instantiated operation, see `cx_between_blocks`.
        """
        return self().get_op("cx_between_blocks")

    def cx_between_blocks(self) -> ExtOp:
        """Targeted CX from the first block to the second. Runtime indices
        select the control and target.
        """
        return self.cx_between_blocks_def.instantiate([])

    @functools.cached_property
    def cx_def(self) -> OpDef:
        """Definition of the `cx` operation.

        For the instantiated operation, see `cx`.
        """
        return self().get_op("cx")

    def cx(self) -> ExtOp:
        """CX from logical qubit 0 to 1."""
        return self.cx_def.instantiate([])

    @functools.cached_property
    def cx_transversal_def(self) -> OpDef:
        """Definition of the `cx_transversal` operation.

        For the instantiated operation, see `cx_transversal`.
        """
        return self().get_op("cx_transversal")

    def cx_transversal(self) -> ExtOp:
        """Apply CX from each logical qubit in the first block to the
        corresponding logical qubit in the second block.
        """
        return self.cx_transversal_def.instantiate([])

    @functools.cached_property
    def cz_def(self) -> OpDef:
        """Definition of the `cz` operation.

        For the instantiated operation, see `cz`.
        """
        return self().get_op("cz")

    def cz(self) -> ExtOp:
        """Logical CZ."""
        return self.cz_def.instantiate([])

    @functools.cached_property
    def free_def(self) -> OpDef:
        """Definition of the `free` operation.

        For the instantiated operation, see `free`.
        """
        return self().get_op("free")

    def free(self) -> ExtOp:
        """Discard a block."""
        return self.free_def.instantiate([])

    @functools.cached_property
    def free_t_state_def(self) -> OpDef:
        """Definition of the `free_t_state` operation.

        For the instantiated operation, see `free_t_state`.
        """
        return self().get_op("free_t_state")

    def free_t_state(self) -> ExtOp:
        """Discard an unused T-state resource."""
        return self.free_t_state_def.instantiate([])

    @functools.cached_property
    def h_all_def(self) -> OpDef:
        """Definition of the `h_all` operation.

        For the instantiated operation, see `h_all`.
        """
        return self().get_op("h_all")

    def h_all(self) -> ExtOp:
        """Hadamard on each logical qubit."""
        return self.h_all_def.instantiate([])

    @functools.cached_property
    def inject_t_def(self) -> OpDef:
        """Definition of the `inject_t` operation.

        For the instantiated operation, see `inject_t`.
        """
        return self().get_op("inject_t")

    def inject_t(self) -> ExtOp:
        """Instantiate the `inject_t` operation.

        Consume a T-state resource and apply T to the logical qubit selected by
        a runtime index.
        """
        return self.inject_t_def.instantiate([])

    @functools.cached_property
    def inject_tdg_def(self) -> OpDef:
        """Definition of the `inject_tdg` operation.

        For the instantiated operation, see `inject_tdg`.
        """
        return self().get_op("inject_tdg")

    def inject_tdg(self) -> ExtOp:
        """Instantiate the `inject_tdg` operation.

        Consume a T-state resource and apply Tdg to the logical qubit selected
        by a runtime index.
        """
        return self.inject_tdg_def.instantiate([])

    @functools.cached_property
    def measure_x_all_def(self) -> OpDef:
        """Definition of the `measure_x_all` operation.

        For the instantiated operation, see `measure_x_all`.
        """
        return self().get_op("measure_x_all")

    def measure_x_all(self) -> ExtOp:
        """Destructively measure both logical qubits in the X basis."""
        return self.measure_x_all_def.instantiate([])

    @functools.cached_property
    def measure_z_all_def(self) -> OpDef:
        """Definition of the `measure_z_all` operation.

        For the instantiated operation, see `measure_z_all`.
        """
        return self().get_op("measure_z_all")

    def measure_z_all(self) -> ExtOp:
        """Destructively measure both logical qubits in the Z basis."""
        return self.measure_z_all_def.instantiate([])

    @functools.cached_property
    def prep_t_state_def(self) -> OpDef:
        """Definition of the `prep_t_state` operation.

        For the instantiated operation, see `prep_t_state`.
        """
        return self().get_op("prep_t_state")

    def prep_t_state(self) -> ExtOp:
        """Instantiate the `prep_t_state` operation.

        Supply a resource which can be consumed to apply a T or Tdg gate to a
        logical qubit.
        """
        return self.prep_t_state_def.instantiate([])

    @functools.cached_property
    def qec_cycle_def(self) -> OpDef:
        """Definition of the `qec_cycle` operation.

        For the instantiated operation, see `qec_cycle`.
        """
        return self().get_op("qec_cycle")

    def qec_cycle(self) -> ExtOp:
        """Perform syndrome extraction and recovery (or a Pauli-frame update).
        Ideally preserves the logical state, including external entanglement.
        """
        return self.qec_cycle_def.instantiate([])

    @functools.cached_property
    def ss_def(self) -> OpDef:
        """Definition of the `ss` operation.

        For the instantiated operation, see `ss`.
        """
        return self().get_op("ss")

    def ss(self) -> ExtOp:
        """Logical S on both qubits."""
        return self.ss_def.instantiate([])

    @functools.cached_property
    def swap_def(self) -> OpDef:
        """Definition of the `swap` operation.

        For the instantiated operation, see `swap`.
        """
        return self().get_op("swap")

    def swap(self) -> ExtOp:
        """Swap the two qubits in the block."""
        return self.swap_def.instantiate([])

    @functools.cached_property
    def x_def(self) -> OpDef:
        """Definition of the `x` operation.

        For the instantiated operation, see `x`.
        """
        return self().get_op("x")

    def x(self) -> ExtOp:
        """Apply X to the logical qubit selected by a runtime index."""
        return self.x_def.instantiate([])

    @functools.cached_property
    def y_def(self) -> OpDef:
        """Definition of the `y` operation.

        For the instantiated operation, see `y`.
        """
        return self().get_op("y")

    def y(self) -> ExtOp:
        """Apply Y to the logical qubit selected by a runtime index."""
        return self.y_def.instantiate([])

    @functools.cached_property
    def z_def(self) -> OpDef:
        """Definition of the `z` operation.

        For the instantiated operation, see `z`.
        """
        return self().get_op("z")

    def z(self) -> ExtOp:
        """Apply Z to the logical qubit selected by a runtime index."""
        return self.z_def.instantiate([])
