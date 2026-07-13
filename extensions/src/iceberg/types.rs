/// Extension providing types for the Iceberg codeblock.
///
/// There are three types defined here:
/// - `block`: The type of a logical code block, parametrized by the number k of
///   logical qubits.
/// - `qubit`: The type of a single logical qubit, belonging to an unknown
///   block. Also referred to as a "dynamic" logical qubit. May be allocated and
///   freed independently, or borrowed from (and later restored to) a block. In
///   the former case, the qubit will be assigned to a block at runtime. In the
///   latter case, the block from which it is borrowed is converted to a
///   `borrowed_block` for as long as any of its logical qubits are borrowed.
/// - `borrowed_block`: The type of a logical code block from which some logical
///   qubits may have been borrowed. May not be used in any logical operations.
///   When all borrowed qubits are returned, this is converted back to a
///   `block`.
use std::sync::{Arc, LazyLock};

use hugr::{
    Extension,
    extension::ExtensionId,
    types::{CustomType, Type, TypeArg, TypeBound, TypeName, type_param::TypeParam},
};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.iceberg.types");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 1);

/// Type name for logical Iceberg block.
pub const BLOCK_TYPENAME: TypeName = TypeName::new_inline("block");

/// Type name for a "borrowed" logical Iceberg block.
pub const BORROWED_BLOCK_TYPENAME: TypeName = TypeName::new_inline("borrowed_block");

/// Type name for an Iceberg pre-block.
pub const PRE_BLOCK_TYPENAME: TypeName = TypeName::new_inline("pre_block");

/// Type name for an Iceberg-encoded logical qubit, either extracted from a
/// block or dynamically allocated.
pub const QUBIT_TYPENAME: TypeName = TypeName::new_inline("qubit");

/// Type of an Iceberg block of a given size.
///
/// * `k_arg` - The number of logical qubits in the code block.
pub fn block_type(k_arg: impl Into<TypeArg>) -> Type {
    CustomType::new(
        BLOCK_TYPENAME,
        [k_arg.into()],
        EXTENSION_ID,
        VERSION,
        TypeBound::Linear,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Type of an Iceberg block of a given size that has been "borrowed". This
/// represents a block from which some logical qubits may have been borrowed; it
/// cannot be used in any logical operations until all those qubits have been
/// returned.
///
/// * `k_arg` - The number of logical qubits in the code block.
pub fn borrowed_block_type(k_arg: impl Into<TypeArg>) -> Type {
    CustomType::new(
        BORROWED_BLOCK_TYPENAME,
        [k_arg.into()],
        EXTENSION_ID,
        VERSION,
        TypeBound::Linear,
        &Arc::<Extension>::downgrade(&EXTENSION),
    )
    .into()
}

/// Type of an Iceberg block of a given size that has not yet been verified to be
/// in a logical state. This represents the state of a block after state preparation
/// but before ancilla qubits have been measured to verify the preparation was successful.
///
/// * `k_arg` - The number of logical qubits in the code block.
pub fn pre_block_type(k_arg: impl Into<TypeArg>) -> Type {
    CustomType::new(
        PRE_BLOCK_TYPENAME,
        [k_arg.into()],
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

/// Extension for logical Iceberg block type.
fn extension() -> Arc<Extension> {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                BLOCK_TYPENAME,
                vec![TypeParam::max_nat_kind()],
                "logical Iceberg block".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                BORROWED_BLOCK_TYPENAME,
                vec![TypeParam::max_nat_kind()],
                "borrowed logical Iceberg block".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                PRE_BLOCK_TYPENAME,
                vec![TypeParam::max_nat_kind()],
                "logical Iceberg pre-block".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        extension
            .add_type(
                QUBIT_TYPENAME,
                vec![],
                "logical Iceberg qubit".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
    })
}

/// Lazy reference to extension for logical Iceberg block type.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(extension);

/// Get an Iceberg block type with size corresponding to a type variable with a
/// given ID.
pub fn block_tv(var_id: usize) -> Type {
    Type::new_extension(
        EXTENSION
            .get_type(&BLOCK_TYPENAME)
            .unwrap()
            .instantiate(vec![TypeArg::new_var_use(
                var_id,
                TypeParam::max_nat_kind(),
            )])
            .unwrap(),
    )
}

/// Get an Iceberg borrowed-block type with size corresponding to a type
/// variable with a given ID.
pub fn borrowed_block_tv(var_id: usize) -> Type {
    Type::new_extension(
        EXTENSION
            .get_type(&BORROWED_BLOCK_TYPENAME)
            .unwrap()
            .instantiate(vec![TypeArg::new_var_use(
                var_id,
                TypeParam::max_nat_kind(),
            )])
            .unwrap(),
    )
}

/// Get an Iceberg pre-block type with size corresponding to a type
/// variable with a given ID.
pub fn pre_block_tv(var_id: usize) -> Type {
    Type::new_extension(
        EXTENSION
            .get_type(&PRE_BLOCK_TYPENAME)
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
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        types::Signature,
    };

    use super::*;

    #[test]
    fn test_iceberg_types_extension() {
        let extn = extension();
        assert_eq!(extn.name() as &str, "guppyft.iceberg.types");
        assert_eq!(extn.types().count(), 4);
        assert_eq!(extn.operations().count(), 0);
    }

    #[test]
    fn test_iceberg_block_type() {
        let block = block_type(6);
        assert!(!block.copyable());
    }

    #[test]
    fn test_iceberg_borrowed_block_type() {
        let borrowed_block = borrowed_block_type(6);
        assert!(!borrowed_block.copyable());
    }

    #[test]
    fn test_iceberg_pre_block_type() {
        let pre_block = pre_block_type(6);
        assert!(!pre_block.copyable());
    }

    #[test]
    fn test_iceberg_qubit_type() {
        let qubit = dynamic_logical_qubit_type();
        assert!(!qubit.copyable());
    }

    #[test]
    fn test_hugr() {
        let block = block_type(2);
        let bblock = borrowed_block_type(2);
        let preblock = pre_block_type(2);
        let qubit = dynamic_logical_qubit_type();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block, bblock, preblock, qubit]);
        let f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        f_build.finish_with_outputs(wires).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
