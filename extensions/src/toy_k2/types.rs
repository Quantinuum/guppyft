/// Extension providing types for logical operations on the ToyK2 code.
use std::sync::{Arc, LazyLock};

use hugr::{
    Extension,
    extension::ExtensionId,
    types::{CustomType, Type, TypeBound, TypeName},
};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.toy_k2.types");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Type name for logical ToyK2 block.
pub const BLOCK_TYPENAME: TypeName = TypeName::new_inline("block");

/// Type of a logical ToyK2 block.
pub fn logical_block_type() -> Type {
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

/// Type name for a measurement of a ToyK2 logical qubit.
pub const QUBIT_MEASUREMENT_TYPENAME: TypeName = TypeName::new_inline("qubit_measurement");

/// Type of a ToyK2 block logical measurement.
pub fn logical_qubit_measurement_type() -> Type {
    CustomType::new(
        QUBIT_MEASUREMENT_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Copyable,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Type name for a measurement of a ToyK2 logical block (both qubits).
pub const BLOCK_MEASUREMENT_TYPENAME: TypeName = TypeName::new_inline("block_measurement");

/// Type of a ToyK2 block logical measurement.
pub fn logical_block_measurement_type() -> Type {
    CustomType::new(
        BLOCK_MEASUREMENT_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Copyable,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Extension for logical types for the ToyK2 code.
fn extension() -> Arc<Extension> {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                BLOCK_TYPENAME,
                vec![],
                "ToyK2 logical block".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                QUBIT_MEASUREMENT_TYPENAME,
                vec![],
                "ToyK2 logical qubit measurement".to_owned(),
                TypeBound::Copyable.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                BLOCK_MEASUREMENT_TYPENAME,
                vec![],
                "ToyK2 logical block measurement".to_owned(),
                TypeBound::Copyable.into(),
                extension_ref,
            )
            .unwrap();
    })
}

/// Lazy reference to the extension for logical types for the ToyK2 code.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(extension);

#[cfg(test)]
mod tests {
    use super::*;
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        types::Signature,
    };

    #[test]
    fn test_toy_k2_types_extension() {
        let extn = extension();
        assert_eq!(extn.name() as &str, "guppyft.toy_k2.types");
        assert_eq!(extn.types().count(), 3);
        assert_eq!(extn.operations().count(), 0);
    }

    #[test]
    fn test_toy_k2_block_type() {
        let qubit = logical_block_type();
        assert!(!qubit.copyable());
    }

    #[test]
    fn test_toy_k2_qubit_measurement_type() {
        let measurement = logical_qubit_measurement_type();
        assert!(measurement.copyable());
    }

    #[test]
    fn test_toy_k2_block_measurement_type() {
        let measurement = logical_block_measurement_type();
        assert!(measurement.copyable());
    }

    #[test]
    fn test_hugr() {
        let block = logical_block_type();
        let qubit_measurement = logical_qubit_measurement_type();
        let block_measurement = logical_block_measurement_type();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block, qubit_measurement, block_measurement]);
        let f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        f_build.finish_with_outputs(wires).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
