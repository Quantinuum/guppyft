//! HUGR extension providing types and logical operations for the `[[20,2,6]]` CSD code.
//!
//! A linear `block` holds two logical qubits. The `prep_zero` operation prepares
//! both qubits in zero, and `x` applies transversal X to a single block.
//! Destructive `measure_z` produces a standard logical measurement of size two;
//! `decode` converts it to two boolean outputs, one per logical qubit.

use std::sync::{Arc, LazyLock, Weak};

use crate::std::types::logical_measurement_type;
use documented::DocumentedVariants;
use hugr::{
    Extension,
    extension::{
        ExtensionId, OpDef, SignatureError, SignatureFunc,
        prelude::bool_t,
        simple_op::{
            HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError,
            try_from_name,
        },
    },
    ops::{ExtensionOp, OpName},
    types::{CustomType, Signature, Type, TypeArg, TypeBound, TypeName, type_param::TermKindError},
};
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.csd");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);
/// Type name for a logical CSD block.
pub const BLOCK_TYPENAME: TypeName = TypeName::new_inline("block");

/// Type of a CSD block containing two logical qubits.
pub fn block_type() -> Type {
    block_type_with_extension(&Arc::downgrade(&EXTENSION))
}

// Use the supplied reference during extension initialization to avoid recursively
// initializing EXTENSION when operation signatures refer to the block type.
fn block_type_with_extension(extension_ref: &Weak<Extension>) -> Type {
    CustomType::new(
        BLOCK_TYPENAME,
        [],
        EXTENSION_ID,
        VERSION,
        TypeBound::Linear,
        extension_ref,
    )
    .into()
}

/// Logical CSD operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum CsdOpDef {
    /// Prepare a block with both logical qubits in the zero state.
    prep_zero,
    /// Apply transversal X to a single block.
    x,
    /// Destructively measure both logical qubits of a block in the Z basis.
    measure_z,
    /// Decode a logical measurement into two booleans, one per logical qubit.
    decode,
}

/// Concrete CSD logical operation.
pub struct ConcreteCsdOp {
    /// The kind of operation.
    pub def: CsdOpDef,
}

impl HasConcrete for CsdOpDef {
    type Concrete = ConcreteCsdOp;

    fn instantiate(&self, args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        if !args.is_empty() {
            return Err(SignatureError::from(TermKindError::WrongNumberArgs(args.len(), 0)).into());
        }
        Ok(self.instantiate_no_args())
    }
}

impl HasDef for ConcreteCsdOp {
    type Def = CsdOpDef;
}

impl MakeExtensionOp for ConcreteCsdOp {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        CsdOpDef::from_def(ext_op.def())?.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        vec![]
    }
}

impl MakeRegisteredOp for ConcreteCsdOp {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl CsdOpDef {
    /// Initialize a concrete CSD operation without type arguments.
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteCsdOp {
        ConcreteCsdOp { def: self }
    }
}

impl MakeOpDef for CsdOpDef {
    fn opdef_id(&self) -> OpName {
        <&Self as Into<&'static str>>::into(self).into()
    }

    fn from_def(op_def: &OpDef) -> Result<Self, OpLoadError> {
        try_from_name(op_def.name(), op_def.extension_id())
    }

    fn extension(&self) -> ExtensionId {
        EXTENSION_ID
    }

    fn extension_ref(&self) -> Weak<Extension> {
        Arc::downgrade(&EXTENSION)
    }

    fn init_signature(&self, extension_ref: &Weak<Extension>) -> SignatureFunc {
        let block = block_type_with_extension(extension_ref);
        match self {
            Self::prep_zero => Signature::new(vec![], vec![block]),
            Self::x => Signature::new(vec![block.clone()], vec![block]),
            Self::measure_z => Signature::new(vec![block], vec![logical_measurement_type(2)]),
            Self::decode => Signature::new(vec![logical_measurement_type(2)], vec![bool_t(); 2]),
        }
        .into()
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for the logical CSD block type and operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                BLOCK_TYPENAME,
                vec![],
                "logical CSD block containing two logical qubits".to_owned(),
                TypeBound::Linear.into(),
                extension_ref,
            )
            .unwrap();
        CsdOpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::std::types::EXTENSION as std_types_extension;
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope},
        ops::DataflowOpTrait,
        package::Package,
        std_extensions::std_reg,
    };
    use std::error::Error;
    use strum::IntoEnumIterator;

    #[test]
    fn test_csd_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.csd");
        assert_eq!(EXTENSION.types().count(), 1);
        assert_eq!(EXTENSION.operations().count(), 4);
        assert!(!block_type().copyable());
        assert_eq!(
            Type::new_extension(
                EXTENSION
                    .get_type(&BLOCK_TYPENAME)
                    .unwrap()
                    .instantiate([])
                    .unwrap()
            ),
            block_type()
        );
    }

    #[test]
    fn test_signatures() {
        for (def, signature) in [
            (
                CsdOpDef::prep_zero,
                Signature::new(vec![], vec![block_type()]),
            ),
            (CsdOpDef::x, Signature::new_endo(vec![block_type()])),
            (
                CsdOpDef::measure_z,
                Signature::new(vec![block_type()], vec![logical_measurement_type(2)]),
            ),
            (
                CsdOpDef::decode,
                Signature::new(vec![logical_measurement_type(2)], vec![bool_t(); 2]),
            ),
        ] {
            let op = def.instantiate_no_args().to_extension_op().unwrap();
            assert_eq!(op.signature().as_ref(), &signature);
            assert_eq!(ConcreteCsdOp::from_extension_op(&op).unwrap().def, def);
        }
    }

    #[test]
    fn test_reject_type_arguments() {
        for def in CsdOpDef::iter() {
            assert!(def.instantiate(&[2.into()]).is_err());
            assert!(
                EXTENSION
                    .instantiate_extension_op(&def.opdef_id(), [2.into()])
                    .is_err()
            );
        }
    }

    #[test]
    fn test_prep_x_measure_decode_serialization() -> Result<(), Box<dyn Error>> {
        let mut module_builder = ModuleBuilder::new();
        let mut f_build =
            module_builder.define_function("main", Signature::new(vec![], vec![bool_t(); 2]))?;
        let prep =
            f_build.add_dataflow_op(EXTENSION.instantiate_extension_op("prep_zero", [])?, [])?;
        let x = f_build
            .add_dataflow_op(EXTENSION.instantiate_extension_op("x", [])?, prep.outputs())?;
        let measurement = f_build.add_dataflow_op(
            EXTENSION.instantiate_extension_op("measure_z", [])?,
            x.outputs(),
        )?;
        let decoded = f_build.add_dataflow_op(
            EXTENSION.instantiate_extension_op("decode", [])?,
            measurement.outputs(),
        )?;
        let [first, second] = decoded.outputs_arr();
        f_build.finish_with_outputs([first, second])?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;

        let package = Package::new([h]);
        let mut bytes = Vec::new();
        write_envelope(
            &mut bytes,
            &package,
            EnvelopeConfig::new(EnvelopeFormat::ModelWithExtensions),
        )?;
        let mut registry = std_reg();
        registry.extend([std_types_extension.clone(), EXTENSION.clone()]);
        let (_, restored) = read_envelope(std::io::BufReader::new(bytes.as_slice()), &registry)?;
        restored.modules[0].validate()?;
        Ok(())
    }
}
