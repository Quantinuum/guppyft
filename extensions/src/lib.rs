//! QEC extensions for HUGRs

//! HUGR extensions for logical operations on QEC codes.
pub mod iceberg;

pub mod steane;

pub mod std;

#[cfg(feature = "cli")]
pub mod cli;

/// Registry containing all extensions defined in this crate, with their real
/// (compiled) signature functions intact.
///
/// This is in contrast to a registry reconstructed from serialized Hugr
/// bytes/JSON, which cannot carry any `SignatureFromArgs`/`CustomFunc`
/// closures (e.g. `guppyft.std.ops.decode`) and instead binds affected ops to
/// a stub that errors when its signature is computed.
pub fn all_extensions() -> hugr::extension::ExtensionRegistry {
    hugr::extension::ExtensionRegistry::new([
        iceberg::types::EXTENSION.to_owned(),
        iceberg::ops::EXTENSION.to_owned(),
        steane::types::EXTENSION.to_owned(),
        steane::ops::EXTENSION.to_owned(),
        std::types::EXTENSION.to_owned(),
        std::ops::EXTENSION.to_owned(),
    ])
}
