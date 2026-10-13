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
    /// Prepare a logical zero state.
    prep_zero,
    /// Prepare a logical |++> state.
    prep_plus,
}
