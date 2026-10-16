//! Types for logical operations on the [[20, 2, 6]] C4-Helix code.
//!
//! A `block` owns two logical qubits, labelled 0 and 1. All code operations
//! act on blocks.
//!
//! A `t_state` owns one magic resource with ideal state
//! (|0> + exp(i*pi/4)|1>)/sqrt(2).
//! Its physical encoding and preparation protocol are chosen by the backend.
//! Both types are linear and have no type parameters.
use std::sync::{Arc, LazyLock};

use hugr::{
    Extension,
    extension::ExtensionId,
    types::{CustomType, Type, TypeBound, TypeName},
};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.helix.types");

/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Type name for a logical Helix block.
pub const BLOCK_TYPENAME: TypeName = TypeName::new_inline("block");

/// Type name for a consumable T-state resource.
pub const T_STATE_TYPENAME: TypeName = TypeName::new_inline("t_state");

/// Type of a magic resource with ideal state (|0> + exp(i*pi/4)|1>)/sqrt(2).
/// This opaque resource does not specify a physical encoding. It can only be
/// prepared, consumed by injection, or explicitly discarded.
pub fn t_state_type() -> Type {
    CustomType::new(
        T_STATE_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Linear,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Type of a Helix block containing exactly two logical qubits.
pub fn block_type() -> Type {
    CustomType::new(
        BLOCK_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Linear,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Extension for logical Helix types.
fn extension() -> Arc<Extension> {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                BLOCK_TYPENAME,
                vec![],
                "logical Helix block".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                T_STATE_TYPENAME,
                vec![],
                "consumable T-state resource with backend-selected encoding".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
    })
}

/// Lazy reference to extension for logical Helix block type.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(extension);

#[cfg(test)]
mod tests {
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        types::Signature,
    };

    use super::*;

    #[test]
    fn test_helix_types_extension() {
        let extn = extension();
        assert_eq!(extn.name() as &str, "guppyft.helix.types");
        assert_eq!(extn.types().count(), 2);
        assert_eq!(extn.operations().count(), 0);
    }

    #[test]
    fn test_helix_block_type() {
        let block = block_type();
        assert!(!block.copyable());
    }

    #[test]
    fn test_t_state_type() {
        let resource = t_state_type();
        assert!(!resource.copyable());
        assert_ne!(resource, block_type());
    }

    #[test]
    fn test_hugr() {
        let block = block_type();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block, t_state_type()]);
        let f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        f_build.finish_with_outputs(wires).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
