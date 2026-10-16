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
        """An opaque, consumable T-state resource with backend-selected encoding.

        For the instantiated type, see `helix_t_state`.
        """
        return self().get_type("t_state")

    def helix_t_state(self) -> ExtType:
        """An opaque, consumable T-state resource with backend-selected encoding."""
        return self.helix_t_state_def.instantiate([])


_HELIX_TYPES = HelixTypesExtension()


class HelixOpsExtension:
    """Extension providing Helix logical operations.

    Logical indices are runtime HUGR inputs, not Python method arguments.
    The block size is always two. Injection includes measurement and
    feed-forward corrections.
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
        """Prepare the |++> state on a block."""
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
        """Instantiate the `cx_between_blocks` operation.

        Targeted CX from the first block to the second. Runtime indices select the
        control and target; the other qubits are unchanged.
        """
        return self.cx_between_blocks_def.instantiate([])

    @functools.cached_property
    def cx_swap_def(self) -> OpDef:
        """Definition of the `cx_swap` operation.

        For the instantiated operation, see `cx_swap`.
        """
        return self().get_op("cx_swap")

    def cx_swap(self) -> ExtOp:
        """CX from logical qubit 0 to 1, then SWAP: |a,b> -> |a XOR b,a>."""
        return self.cx_swap_def.instantiate([])

    @functools.cached_property
    def cx_transversal_def(self) -> OpDef:
        """Definition of the `cx_transversal` operation.

        For the instantiated operation, see `cx_transversal`.
        """
        return self().get_op("cx_transversal")

    def cx_transversal(self) -> ExtOp:
        """Instantiate the `cx_transversal` operation.

        Apply CX from each logical qubit in the first block to the corresponding
        logical qubit in the second block, preserving block order.
        """
        return self.cx_transversal_def.instantiate([])

    @functools.cached_property
    def cz_def(self) -> OpDef:
        """Definition of the `cz` operation.

        For the instantiated operation, see `cz`.
        """
        return self().get_op("cz")

    def cz(self) -> ExtOp:
        """Instantiate the `cz` operation.

        Logical CZ: |a,b> -> (-1)^(ab)|a,b>. Lowering must compensate the physical
        gadget's residual Z on qubit 1.
        """
        return self.cz_def.instantiate([])

    @functools.cached_property
    def free_def(self) -> OpDef:
        """Definition of the `free` operation.

        For the instantiated operation, see `free`.
        """
        return self().get_op("free")

    def free(self) -> ExtOp:
        """Discard a block in any logical state."""
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
    def hh_swap_def(self) -> OpDef:
        """Definition of the `hh_swap` operation.

        For the instantiated operation, see `hh_swap`.
        """
        return self().get_op("hh_swap")

    def hh_swap(self) -> ExtOp:
        """Hadamard on each logical qubit followed by SWAP."""
        return self.hh_swap_def.instantiate([])

    @functools.cached_property
    def inject_t_def(self) -> OpDef:
        """Definition of the `inject_t` operation.

        For the instantiated operation, see `inject_t`.
        """
        return self().get_op("inject_t")

    def inject_t(self) -> ExtOp:
        """Instantiate the `inject_t` operation.

        Consume a T-state resource and apply T = diag(1, exp(i*pi/4)) to the logical
        qubit selected by a runtime index, preserving its block partner. Inputs are
        (block, index, resource); measurement and feed-forward corrections are
        included, leaving no outstanding Clifford correction.
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

        Consume the same T-state resource as inject_t and apply T dagger to the
        indexed logical qubit, preserving its block partner. Inputs are (block,
        index, resource); all measurement and Clifford corrections are included.
        """
        return self.inject_tdg_def.instantiate([])

    @functools.cached_property
    def measure_xx_def(self) -> OpDef:
        """Definition of the `measure_xx` operation.

        For the instantiated operation, see `measure_xx`.
        """
        return self().get_op("measure_xx")

    def measure_xx(self) -> ExtOp:
        """Instantiate the `measure_xx` operation.

        Destructively measure both logical qubits in the X basis. Return a two-
        outcome logical measurement, ordered by logical index. Decoded bit b denotes
        eigenvalue (-1)^b; this is not an XX parity measurement.
        """
        return self.measure_xx_def.instantiate([])

    @functools.cached_property
    def measure_zz_def(self) -> OpDef:
        """Definition of the `measure_zz` operation.

        For the instantiated operation, see `measure_zz`.
        """
        return self().get_op("measure_zz")

    def measure_zz(self) -> ExtOp:
        """Instantiate the `measure_zz` operation.

        Destructively measure both logical qubits in the Z basis. Return a two-
        outcome logical measurement, ordered by logical index. Decoded bit b denotes
        eigenvalue (-1)^b; this is not a ZZ parity measurement.
        """
        return self.measure_zz_def.instantiate([])

    @functools.cached_property
    def prep_t_state_def(self) -> OpDef:
        """Definition of the `prep_t_state` operation.

        For the instantiated operation, see `prep_t_state`.
        """
        return self().get_op("prep_t_state")

    def prep_t_state(self) -> ExtOp:
        """Instantiate the `prep_t_state` operation.

        Supply a resource with ideal state (|0> + exp(i*pi/4)|1>)/sqrt(2). The
        backend chooses the factory and encoding, and handles heralded retries.
        Preparation need not occur inside a Helix block.
        """
        return self.prep_t_state_def.instantiate([])

    @functools.cached_property
    def qec_cycle_def(self) -> OpDef:
        """Definition of the `qec_cycle` operation.

        For the instantiated operation, see `qec_cycle`.
        """
        return self().get_op("qec_cycle")

    def qec_cycle(self) -> ExtOp:
        """Instantiate the `qec_cycle` operation.

        Perform syndrome extraction and recovery (or a Pauli-frame update). Ideally
        preserves the logical state, including external entanglement.
        """
        return self.qec_cycle_def.instantiate([])

    @functools.cached_property
    def ss_def(self) -> OpDef:
        """Definition of the `ss` operation.

        For the instantiated operation, see `ss`.
        """
        return self().get_op("ss")

    def ss(self) -> ExtOp:
        """Instantiate the `ss` operation.

        Logical S on both qubits: |a,b> -> i^(a+b)|a,b>. Lowering must compensate
        the physical gadget's residual Z on both qubits and include the flagging and
        syndrome extraction required for fault tolerance.
        """
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
