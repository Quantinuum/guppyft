/// Extension providing standard types for guppyft
///
/// Types defined are:
/// - `LogicalMeasurement`:
use hugr::Extension;
use hugr::extension::ExtensionId;
use hugr::types::type_param::TypeParam;
use hugr::types::{CustomType, Type, TypeArg, TypeBound, TypeName};
use std::sync::{Arc, LazyLock};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.std.types");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);
/// Type name for a logical measurement.
pub const LOGICAL_MEASUREMENT_TYPENAME: TypeName = TypeName::new_inline("logical_measurement");

/// Logical measurement type of a given size.
///
/// * `k_arg` - The number of logical measurements.
pub fn logical_measurement_type(k_arg: impl Into<TypeArg>) -> Type {
    CustomType::new(
        LOGICAL_MEASUREMENT_TYPENAME,
        [k_arg.into()],
        EXTENSION_ID,
        VERSION,
        TypeBound::Copyable,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Extension for guppyft std types.
fn extension() -> Arc<Extension> {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                LOGICAL_MEASUREMENT_TYPENAME,
                vec![TypeParam::max_nat_kind()],
                "logical measurement".to_owned(),
                TypeBound::Copyable.into(),
                extension_ref,
            )
            .unwrap();
    })
}

/// Lazy reference to extension for guppyft std types.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(extension);

/// Get a logical measurement type with size corresponding to a type variable with a
/// given ID.
pub fn logical_measurement_tv(var_id: usize) -> Type {
    Type::new_extension(
        EXTENSION
            .get_type(&LOGICAL_MEASUREMENT_TYPENAME)
            .unwrap()
            .instantiate(vec![TypeArg::new_var_use(
                var_id,
                TypeParam::max_nat_kind(),
            )])
            .unwrap(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use hugr::HugrView;
    use hugr::builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder};
    use hugr::types::Signature;

    #[test]
    fn test_std_types_extension() {
        let extn = extension();
        assert_eq!(extn.name() as &str, "guppyft.std.types");
        assert_eq!(extn.types().count(), 1);
        assert_eq!(extn.operations().count(), 0);
    }

    #[test]
    fn test_logical_measurement_type() {
        let meas = logical_measurement_type(2);
        assert!(meas.copyable());
    }

    #[test]
    fn test_hugr() {
        let meas = logical_measurement_type(2);
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![meas.clone()]);
        let foo = module_builder.define_function("foo", signature).unwrap();
        let output = foo.input_wires().clone();
        foo.finish_with_outputs(output).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
