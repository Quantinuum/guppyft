//! HUGR extension providing types and logical operations for the `[[20,2,6]]` CSD code.
//!
//! A linear `block` holds two logical qubits. The `prep_zero` operation prepares
//! both qubits in zero.
//! Destructive `measure_z` returns two boolean outputs, one per logical qubit.
//!
//! Transversal CNOT acts on corresponding logical qubits of two blocks; global
//! S and T act on both logical qubits of one block. Targeted operations take
//! static logical-qubit indices (0 or 1). Targeted CNOT takes a control index
//! in the first block and a target index in the second block. Targeted Z
//! measurement preserves the block and returns one boolean result.
//!
//! `prep_magic_state` prepares a block containing two T magic states. Both T
//! operations take the data block first and the magic block second, consume the
//! magic block, and return only the data block. Targeted T uses magic slot 0
//! and discards the unused resource slot.

use std::{
    num::NonZeroU64,
    sync::{Arc, LazyLock, Weak},
};

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
    types::{
        CustomType, PolyFuncTypeRV, Signature, Type, TypeArg, TypeBound, TypeName,
        type_param::{TermKindError, TypeParam, check_term_kind},
    },
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
    /// Prepare a block with both logical qubits in the T magic state T|+>.
    prep_magic_state,
    /// Destructively measure both logical qubits in Z, returning two booleans in logical-qubit order.
    measure_z,
    /// Apply CNOT transversally from the first block to the second block.
    transversal_cnot,
    /// Apply CNOT between the indexed control in the first block and target in the second.
    targeted_cnot,
    /// Apply S to both logical qubits in a block.
    global_s,
    /// Apply T to both data qubits by injection, consuming the second (magic) block.
    global_t,
    /// Apply T to the indexed data qubit using magic slot 0, consuming the second block.
    targeted_t,
    /// Apply H to the indexed logical qubit in a block.
    targeted_h,
    /// Non-destructively measure the indexed logical qubit in Z, returning the block and a boolean.
    targeted_measure_z,
}

/// Concrete CSD logical operation.
pub struct ConcreteCsdOp {
    /// The kind of operation.
    pub def: CsdOpDef,
    /// Static logical-qubit indices, in control/target order for targeted CNOT.
    pub indices: Vec<TypeArg>,
}

impl HasConcrete for CsdOpDef {
    type Concrete = ConcreteCsdOp;

    fn instantiate(&self, args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        let params = self.index_params();
        if args.len() != params.len() {
            return Err(SignatureError::from(TermKindError::WrongNumberArgs(
                args.len(),
                params.len(),
            ))
            .into());
        }
        for (arg, param) in args.iter().zip(&params) {
            check_term_kind(arg, param).map_err(SignatureError::from)?;
        }
        Ok(ConcreteCsdOp {
            def: *self,
            indices: args.to_vec(),
        })
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
        self.indices.clone()
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
    fn index_params(self) -> Vec<TypeParam> {
        let count = match self {
            Self::targeted_cnot => 2,
            Self::targeted_t | Self::targeted_h | Self::targeted_measure_z => 1,
            _ => 0,
        };
        vec![TypeParam::bounded_nat_kind(NonZeroU64::new(2).unwrap()); count]
    }

    /// Initialize a concrete CSD operation without type arguments.
    ///
    /// # Panics
    /// Panics for targeted operations, which require logical-qubit indices.
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteCsdOp {
        self.instantiate(&[])
            .expect("targeted CSD operations require logical-qubit indices")
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
        let signature = match self {
            Self::prep_zero | Self::prep_magic_state => Signature::new(vec![], vec![block]),
            Self::global_s | Self::targeted_h => Signature::new_endo(vec![block]),
            Self::global_t | Self::targeted_t => {
                Signature::new(vec![block.clone(); 2], vec![block])
            }
            Self::transversal_cnot | Self::targeted_cnot => Signature::new_endo(vec![block; 2]),
            Self::measure_z => Signature::new(vec![block], vec![bool_t(); 2]),
            Self::targeted_measure_z => Signature::new(vec![block.clone()], vec![block, bool_t()]),
        };
        PolyFuncTypeRV::new(self.index_params(), signature).into()
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
        assert_eq!(EXTENSION.operations().count(), 10);
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
            (
                CsdOpDef::measure_z,
                Signature::new(vec![block_type()], vec![bool_t(); 2]),
            ),
            (
                CsdOpDef::transversal_cnot,
                Signature::new_endo(vec![block_type(); 2]),
            ),
            (CsdOpDef::global_s, Signature::new_endo(vec![block_type()])),
            (
                CsdOpDef::global_t,
                Signature::new(vec![block_type(); 2], vec![block_type()]),
            ),
        ] {
            let op = def.instantiate_no_args().to_extension_op().unwrap();
            assert_eq!(op.signature().as_ref(), &signature);
            assert_eq!(ConcreteCsdOp::from_extension_op(&op).unwrap().def, def);
        }
    }

    #[test]
    fn test_targeted_signatures() {
        for index in 0..2 {
            for (def, signature) in [
                (
                    CsdOpDef::targeted_t,
                    Signature::new(vec![block_type(); 2], vec![block_type()]),
                ),
                (
                    CsdOpDef::targeted_h,
                    Signature::new_endo(vec![block_type()]),
                ),
                (
                    CsdOpDef::targeted_measure_z,
                    Signature::new(vec![block_type()], vec![block_type(), bool_t()]),
                ),
            ] {
                check_targeted_op(def, vec![index.into()], signature);
            }
            for target in 0..2 {
                check_targeted_op(
                    CsdOpDef::targeted_cnot,
                    vec![index.into(), target.into()],
                    Signature::new_endo(vec![block_type(); 2]),
                );
            }
        }
    }

    fn check_targeted_op(def: CsdOpDef, args: Vec<TypeArg>, signature: Signature) {
        let concrete = def.instantiate(&args).unwrap();
        let op = concrete.to_extension_op().unwrap();
        assert_eq!(op.signature().as_ref(), &signature);
        let restored = ConcreteCsdOp::from_extension_op(&op).unwrap();
        assert_eq!(restored.def, def);
        assert_eq!(restored.type_args(), args);
        assert_eq!(
            EXTENSION
                .instantiate_extension_op(&def.opdef_id(), args)
                .unwrap()
                .signature()
                .as_ref(),
            &signature
        );
    }

    #[test]
    fn test_reject_type_arguments() {
        for def in CsdOpDef::iter() {
            let count = def.index_params().len();
            let mut invalid_args = vec![vec![0.into(); count + 1]];
            if count > 0 {
                invalid_args.push(vec![0.into(); count - 1]);
                for index in 0..count {
                    for invalid in [2.into(), u64::MAX.into(), bool_t().into()] {
                        let mut args = vec![0.into(); count];
                        args[index] = invalid;
                        invalid_args.push(args);
                    }
                }
            }
            for args in invalid_args {
                assert!(def.instantiate(&args).is_err(), "{def:?}: {args:?}");
                assert!(
                    EXTENSION
                        .instantiate_extension_op(&def.opdef_id(), args.clone())
                        .is_err(),
                    "{def:?}: {args:?}"
                );
            }
        }
    }

    #[test]
    fn test_ops_serialization() -> Result<(), Box<dyn Error>> {
        let mut module_builder = ModuleBuilder::new();
        let mut f_build =
            module_builder.define_function("main", Signature::new(vec![], vec![bool_t(); 5]))?;
        let mut blocks = Vec::new();
        for _ in 0..2 {
            let [block] = f_build
                .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_zero", [])?, [])?
                .outputs_arr();
            blocks.push(block);
        }
        for (name, args) in [
            ("transversal_cnot", vec![]),
            ("targeted_cnot", vec![0.into(), 1.into()]),
        ] {
            blocks = f_build
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, args)?, blocks)?
                .outputs()
                .collect();
        }
        for (name, args) in [("global_s", vec![]), ("targeted_h", vec![0.into()])] {
            [blocks[0]] = f_build
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, args)?, [blocks[0]])?
                .outputs_arr();
        }
        for (name, args) in [("global_t", vec![]), ("targeted_t", vec![1.into()])] {
            let [magic] = f_build
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op("prep_magic_state", [])?,
                    [],
                )?
                .outputs_arr();
            [blocks[0]] = f_build
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op(name, args)?,
                    [blocks[0], magic],
                )?
                .outputs_arr();
        }
        let [block, measurement] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("targeted_measure_z", [0.into()])?,
                [blocks[0]],
            )?
            .outputs_arr();
        blocks[0] = block;
        let mut outputs = vec![measurement];
        for block in blocks {
            let measurement = f_build.add_dataflow_op(
                EXTENSION.instantiate_extension_op("measure_z", [])?,
                [block],
            )?;
            outputs.extend(measurement.outputs());
        }
        f_build.finish_with_outputs(outputs)?;
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
        registry.extend([EXTENSION.clone()]);
        let (_, restored) = read_envelope(std::io::BufReader::new(bytes.as_slice()), &registry)?;
        restored.modules[0].validate()?;
        Ok(())
    }
}
