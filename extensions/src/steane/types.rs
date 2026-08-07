/// Extension providing types for logical operations on the Steane code.
///
/// Currently, there is only a single type defined here:
/// - `qubit`: The type of a logical Steane qubit.
use std::sync::{Arc, LazyLock};

use hugr::{
    Extension,
    extension::ExtensionId,
    types::{CustomType, Type, TypeBound, TypeName},
};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.steane.types");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Type name for a Steane-encoded logical qubit.
pub const QUBIT_TYPENAME: TypeName = TypeName::new_inline("qubit");

/// Type of a logical Steane qubit.
pub fn logical_qubit_type() -> Type {
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

/// Type name for a measurement of a Steane qubit.
pub const MEASUREMENT_TYPENAME: TypeName = TypeName::new_inline("measurement");

/// Type of a logical Steane measurement.
pub fn logical_measurement_type() -> Type {
    CustomType::new(
        MEASUREMENT_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Copyable,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Extension for logical types for the Steane code.
fn extension() -> Arc<Extension> {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                QUBIT_TYPENAME,
                vec![],
                "logical Steane qubit".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                MEASUREMENT_TYPENAME,
                vec![],
                "logical Steane measurement".to_owned(),
                TypeBound::Copyable.into(),
                extension_ref,
            )
            .unwrap();
    })
}

/// Lazy reference to the extension for logical types for the Steane code.
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
    fn test_steane_types_extension() {
        let extn = extension();
        assert_eq!(extn.name() as &str, "guppyft.steane.types");
        assert_eq!(extn.types().count(), 2);
        assert_eq!(extn.operations().count(), 0);
    }

    #[test]
    fn test_steane_qubit_type() {
        let qubit = logical_qubit_type();
        assert!(!qubit.copyable());
    }
    #[test]
    fn test_steane_measurement_type() {
        let measurement = logical_measurement_type();
        assert!(measurement.copyable());
    }

    #[test]
    fn test_hugr() {
        let qubit = logical_qubit_type();
        let measurement = logical_measurement_type();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![qubit, measurement]);
        let f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        f_build.finish_with_outputs(wires).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
