/// Extension providing types for logical operations on the C4-Helix code.
use std::sync::{Arc, LazyLock};

use hugr::{
    Extension,
    extension::ExtensionId,
    types::{CustomType, Type, TypeBound, TypeName, type_param::TypeParam},
};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.helix.types");

/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Type name for logical Iceberg block.
pub const BLOCK_TYPENAME: TypeName = TypeName::new_inline("block");

/// Type name for a Helix-encoded logical qubit, either extracted from a block
/// or dynamically allocated.
pub const QUBIT_TYPENAME: TypeName = TypeName::new_inline("qubit");

/// Type of a Helix block.
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

/// Type of a "dynamic" logical qubit. This represents a logical qubit whose
/// block is not statically known (but assigned at runtime). It may have been
/// "borrowed" from a logical block, or allocated independently.
pub fn dynamic_logical_qubit_type() -> Type {
    CustomType::new(
        QUBIT_TYPENAME,
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
                QUBIT_TYPENAME,
                vec![],
                "logical Helix qubit".to_owned(),
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
    fn test_helix_qubit_type() {
        let qubit = dynamic_logical_qubit_type();
        assert!(!qubit.copyable());
    }

    #[test]
    fn test_hugr() {
        let block = block_type();
        let qubit = dynamic_logical_qubit_type();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block, qubit]);
        let f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        f_build.finish_with_outputs(wires).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
