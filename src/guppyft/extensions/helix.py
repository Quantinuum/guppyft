"""Python bindings for the C4-Helix HUGR types and operations extensions."""

import functools

from hugr.ext import Extension, ExtensionRegistry, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.std.int import INT_TYPES_EXTENSION, int_t
from hugr.tys import BoundedNatArg, ExtType, FunctionType

from ._util import load_extension, load_extension_json


class HelixTypesExtension:
    """Extension providing linear Helix blocks, qubits, and T-state resources."""

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
    def helix_borrowed_block_def(self) -> TypeDef:
        """A Helix block unavailable to block operations until restoration.

        For the instantiated type, see `helix_borrowed_block`.
        """
        return self().get_type("borrowed_block")

    def helix_borrowed_block(self) -> ExtType:
        """A Helix block unavailable to block operations until restoration."""
        return self.helix_borrowed_block_def.instantiate([])

    @functools.cached_property
    def helix_qubit_def(self) -> TypeDef:
        """A dynamic Helix logical qubit with runtime block membership.

        For the instantiated type, see `helix_qubit`.
        """
        return self().get_type("qubit")

    def helix_qubit(self) -> ExtType:
        """A dynamic Helix logical qubit with runtime block membership."""
        return self.helix_qubit_def.instantiate([])

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


def _validate_count(m: int) -> None:
    if not 0 <= m <= 2:
        raise ValueError("The number of Helix logical qubits must be between 0 and 2.")


class HelixOpsExtension:
    """Extension providing Helix logical operations.

    Logical indices are runtime HUGR inputs, not Python method arguments.
    Only borrow/restore operations take a static count ``m``; the block size
    is always two. Injection includes measurement and feed-forward corrections.
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
    def alloc_dynq_def(self) -> OpDef:
        """Definition of the `alloc_dynq` operation.

        For the instantiated operation, see `alloc_dynq`.
        """
        return self().get_op("alloc_dynq")

    def alloc_dynq(self) -> ExtOp:
        """Instantiate the `alloc_dynq` operation.

        Allocate a dynamic logical qubit in the |0> state. Its physical block and
        logical position are assigned at runtime.
        """
        return self.alloc_dynq_def.instantiate([])

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
    def borrow_def(self) -> OpDef:
        """Definition of the `borrow` operation.

        For the instantiated operation, see `borrow`.
        """
        return self().get_op("borrow")

    def borrow(self, m: int) -> ExtOp:
        """Instantiate the `borrow` operation.

        Borrow m logical qubits selected by distinct runtime indices (0 or 1). Takes
        a block followed by m indices; returns a borrowed block followed by m
        dynamic qubits in index-input order. Static parameter m is in 0..=2.
        Preserves the joint state and each qubit's originating block and index.

        Args:
            m: Number of logical qubits to borrow, from 0 to 2.

        Raises:
            ValueError: If m is outside 0..=2.
        """
        _validate_count(m)
        return self.borrow_def.instantiate(
            args=[BoundedNatArg(m)],
            concrete_signature=FunctionType(
                [_HELIX_TYPES.helix_block(), *([int_t(6)] * m)],
                [
                    _HELIX_TYPES.helix_borrowed_block(),
                    *([_HELIX_TYPES.helix_qubit()] * m),
                ],
            ),
        )

    @functools.cached_property
    def borrow_more_def(self) -> OpDef:
        """Definition of the `borrow_more` operation.

        For the instantiated operation, see `borrow_more`.
        """
        return self().get_op("borrow_more")

    def borrow_more(self, m: int) -> ExtOp:
        """Instantiate the `borrow_more` operation.

        Borrow m additional logical qubits from a borrowed block. Takes a borrowed
        block followed by m distinct, currently unborrowed indices; returns the
        borrowed block followed by m dynamic qubits in index-input order. Invalid
        indices or outstanding borrows of those indices cause a runtime panic.

        Args:
            m: Number of logical qubits to borrow, from 0 to 2.

        Raises:
            ValueError: If m is outside 0..=2.
        """
        _validate_count(m)
        return self.borrow_more_def.instantiate(
            args=[BoundedNatArg(m)],
            concrete_signature=FunctionType(
                [_HELIX_TYPES.helix_borrowed_block(), *([int_t(6)] * m)],
                [
                    _HELIX_TYPES.helix_borrowed_block(),
                    *([_HELIX_TYPES.helix_qubit()] * m),
                ],
            ),
        )

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
    def cx_dynq_def(self) -> OpDef:
        """Definition of the `cx_dynq` operation.

        For the instantiated operation, see `cx_dynq`.
        """
        return self().get_op("cx_dynq")

    def cx_dynq(self) -> ExtOp:
        """Instantiate the `cx_dynq` operation.

        Apply logical CX with the first dynamic qubit controlling the second. The
        inputs may belong to the same block or different blocks.
        """
        return self.cx_dynq_def.instantiate([])

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
    def cz_dynq_def(self) -> OpDef:
        """Definition of the `cz_dynq` operation.

        For the instantiated operation, see `cz_dynq`.
        """
        return self().get_op("cz_dynq")

    def cz_dynq(self) -> ExtOp:
        """Instantiate the `cz_dynq` operation.

        Apply logical CZ to two dynamic qubits, regardless of block membership.
        """
        return self.cz_dynq_def.instantiate([])

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
    def free_dynq_def(self) -> OpDef:
        """Definition of the `free_dynq` operation.

        For the instantiated operation, see `free_dynq`.
        """
        return self().get_op("free_dynq")

    def free_dynq(self) -> ExtOp:
        """Instantiate the `free_dynq` operation.

        Discard a dynamic logical qubit in any state without changing its partner.
        """
        return self.free_dynq_def.instantiate([])

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
    def h_dynq_def(self) -> OpDef:
        """Definition of the `h_dynq` operation.

        For the instantiated operation, see `h_dynq`.
        """
        return self().get_op("h_dynq")

    def h_dynq(self) -> ExtOp:
        """Instantiate the `h_dynq` operation.

        Apply logical Hadamard to a dynamic qubit, leaving its block partner
        unchanged.
        """
        return self.h_dynq_def.instantiate([])

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
    def inject_t_dynq_def(self) -> OpDef:
        """Definition of the `inject_t_dynq` operation.

        For the instantiated operation, see `inject_t_dynq`.
        """
        return self().get_op("inject_t_dynq")

    def inject_t_dynq(self) -> ExtOp:
        """Instantiate the `inject_t_dynq` operation.

        Consume a T-state resource and apply T to a dynamic logical qubit. Inputs
        are (qubit, resource). Preserves its partner and includes all measurement,
        feed-forward, and Clifford corrections.
        """
        return self.inject_t_dynq_def.instantiate([])

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
    def inject_tdg_dynq_def(self) -> OpDef:
        """Definition of the `inject_tdg_dynq` operation.

        For the instantiated operation, see `inject_tdg_dynq`.
        """
        return self().get_op("inject_tdg_dynq")

    def inject_tdg_dynq(self) -> ExtOp:
        """Instantiate the `inject_tdg_dynq` operation.

        Consume a T-state resource and apply T dagger to a dynamic logical qubit.
        Inputs are (qubit, resource). Preserves its partner and includes all
        measurement, feed-forward, and Clifford corrections.
        """
        return self.inject_tdg_dynq_def.instantiate([])

    @functools.cached_property
    def measure_x_dynq_def(self) -> OpDef:
        """Definition of the `measure_x_dynq` operation.

        For the instantiated operation, see `measure_x_dynq`.
        """
        return self().get_op("measure_x_dynq")

    def measure_x_dynq(self) -> ExtOp:
        """Instantiate the `measure_x_dynq` operation.

        Destructively measure a dynamic qubit in the X basis, preserving its
        partner. The decoded bit b denotes eigenvalue (-1)^b.
        """
        return self.measure_x_dynq_def.instantiate([])

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
    def measure_z_dynq_def(self) -> OpDef:
        """Definition of the `measure_z_dynq` operation.

        For the instantiated operation, see `measure_z_dynq`.
        """
        return self().get_op("measure_z_dynq")

    def measure_z_dynq(self) -> ExtOp:
        """Instantiate the `measure_z_dynq` operation.

        Destructively measure a dynamic qubit in the Z basis, preserving its
        partner. The decoded bit b denotes eigenvalue (-1)^b.
        """
        return self.measure_z_dynq_def.instantiate([])

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
    def restore_def(self) -> OpDef:
        """Definition of the `restore` operation.

        For the instantiated operation, see `restore`.
        """
        return self().get_op("restore")

    def restore(self, m: int) -> ExtOp:
        """Instantiate the `restore` operation.

        Return the final m borrowed qubits and recover the owning block. Takes the
        borrowed block followed by m qubits; returns a block. Panics at runtime for
        invalid provenance or remaining outstanding borrows. All borrow/restore
        operations have a single static count m in 0..=2.

        Args:
            m: Number of logical qubits to restore, from 0 to 2.

        Raises:
            ValueError: If m is outside 0..=2.
        """
        _validate_count(m)
        return self.restore_def.instantiate(
            args=[BoundedNatArg(m)],
            concrete_signature=FunctionType(
                [
                    _HELIX_TYPES.helix_borrowed_block(),
                    *([_HELIX_TYPES.helix_qubit()] * m),
                ],
                [_HELIX_TYPES.helix_block(), *([])],
            ),
        )

    @functools.cached_property
    def restore_some_def(self) -> OpDef:
        """Definition of the `restore_some` operation.

        For the instantiated operation, see `restore_some`.
        """
        return self().get_op("restore_some")

    def restore_some(self, m: int) -> ExtOp:
        """Instantiate the `restore_some` operation.

        Return m borrowed qubits to their originating block and logical positions.
        Takes the borrowed block followed by m qubits; returns the borrowed block.
        Qubit order is immaterial; wrong-block or invalid handles cause a runtime
        panic.

        Args:
            m: Number of logical qubits to restore, from 0 to 2.

        Raises:
            ValueError: If m is outside 0..=2.
        """
        _validate_count(m)
        return self.restore_some_def.instantiate(
            args=[BoundedNatArg(m)],
            concrete_signature=FunctionType(
                [
                    _HELIX_TYPES.helix_borrowed_block(),
                    *([_HELIX_TYPES.helix_qubit()] * m),
                ],
                [_HELIX_TYPES.helix_borrowed_block(), *([])],
            ),
        )

    @functools.cached_property
    def s_dynq_def(self) -> OpDef:
        """Definition of the `s_dynq` operation.

        For the instantiated operation, see `s_dynq`.
        """
        return self().get_op("s_dynq")

    def s_dynq(self) -> ExtOp:
        """Instantiate the `s_dynq` operation.

        Apply logical S = diag(1, i) to a dynamic qubit, leaving its partner
        unchanged.
        """
        return self.s_dynq_def.instantiate([])

    @functools.cached_property
    def sdg_dynq_def(self) -> OpDef:
        """Definition of the `sdg_dynq` operation.

        For the instantiated operation, see `sdg_dynq`.
        """
        return self().get_op("sdg_dynq")

    def sdg_dynq(self) -> ExtOp:
        """Apply logical S dagger = diag(1, -i) to a dynamic qubit."""
        return self.sdg_dynq_def.instantiate([])

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
    def swap_dynq_def(self) -> OpDef:
        """Definition of the `swap_dynq` operation.

        For the instantiated operation, see `swap_dynq`.
        """
        return self().get_op("swap_dynq")

    def swap_dynq(self) -> ExtOp:
        """Instantiate the `swap_dynq` operation.

        Exchange the logical states of two dynamic qubits, preserving output order.
        """
        return self.swap_dynq_def.instantiate([])

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
    def x_dynq_def(self) -> OpDef:
        """Definition of the `x_dynq` operation.

        For the instantiated operation, see `x_dynq`.
        """
        return self().get_op("x_dynq")

    def x_dynq(self) -> ExtOp:
        """Instantiate the `x_dynq` operation.

        Apply logical X to a dynamic qubit, leaving its block partner unchanged.
        """
        return self.x_dynq_def.instantiate([])

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
    def y_dynq_def(self) -> OpDef:
        """Definition of the `y_dynq` operation.

        For the instantiated operation, see `y_dynq`.
        """
        return self().get_op("y_dynq")

    def y_dynq(self) -> ExtOp:
        """Instantiate the `y_dynq` operation.

        Apply logical Y to a dynamic qubit, leaving its block partner unchanged.
        """
        return self.y_dynq_def.instantiate([])

    @functools.cached_property
    def z_def(self) -> OpDef:
        """Definition of the `z` operation.

        For the instantiated operation, see `z`.
        """
        return self().get_op("z")

    def z(self) -> ExtOp:
        """Apply Z to the logical qubit selected by a runtime index."""
        return self.z_def.instantiate([])

    @functools.cached_property
    def z_dynq_def(self) -> OpDef:
        """Definition of the `z_dynq` operation.

        For the instantiated operation, see `z_dynq`.
        """
        return self().get_op("z_dynq")

    def z_dynq(self) -> ExtOp:
        """Instantiate the `z_dynq` operation.

        Apply logical Z to a dynamic qubit, leaving its block partner unchanged.
        """
        return self.z_dynq_def.instantiate([])
