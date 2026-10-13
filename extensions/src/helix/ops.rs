/// Extension providing logical operations on C4-Helix codeblocks.
use documented::DocumentedVariants;
use hugr::extension::ExtensionId;
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.helix.ops");

/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Logical Helix operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum HelixOpDef {
    /// Prepare the all-zero state on a block.
    alloc_zero,
    /// Prepare the |++> state on a block.
    alloc_plus,
    /// Free a block.
    free,
    /// X gate.
    x,
    /// Y gate.
    y,
    /// Z gate.
    z,
    /// Swap the two qubits in the block.
    swap,
    /// CX (with control on qubit 0) followed by swap.
    cx_swap,
    /// H on each qubit followed by swap
    hh_swap,
    /// CZ gate.
    cz,
    /// S on each qubit.
    ss,
    /// CX gate involving two blocks.
    cx_between_blocks,
    /// CX gate applied transversally over two blocks.
    cx_transversal,
    /// Prepare a state that can be used to produce T and Tdg states.
    prep_t_state,
    /// Perform a T gate by injecting a magic state.
    inject_t,
    /// Perform a Tdg gate by injecting a magic state.
    inject_tdg,
    /// Measurement of both qubits in the X basis.
    measure_xx,
    /// Measurement of both qubits in the Z basis.
    measure_zz,
    /// Perform a QEC cycle on a block.
    qec_cycle,
}
