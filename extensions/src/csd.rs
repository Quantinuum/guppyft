//! HUGR extension providing types and logical operations for the CSD code.
//!
//! Each linear `qubit` wire represents one logical qubit. `prep_zero` prepares
//! the two qubits of a block as one `(qubit, qubit)` tuple; destructive `measure_z`
//! consumes that tuple and returns two booleans in slot order.
//!
//! Global S and T act on a data tuple. Transversal CNOT takes a control tuple
//! first, then a target tuple, and acts on corresponding slots. Targeted operations
//! take only the qubits they act on, without static slot indices. Targeted Z
//! measurement preserves its qubit and returns one boolean result.
//!
//! `prep_magic_state` prepares a tuple of two T magic qubits. Global T consumes
//! a magic tuple; targeted T also consumes a full tuple, using slot 0 for injection
//! and discarding the unused resource in slot 1. Both return only the data.
//! Tuple members must occupy slots 0 and 1 of the same block. The tuple type
//! expresses this grouping, but checking block membership is left to the pipeline.
//!
//! The `_single` preparation and destructive measurement operations expose only
//! one logical qubit, without an implicit partner wire. Physical block allocation
//! and release are left to the downstream pipeline.

use std::sync::{Arc, LazyLock, Weak};

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
/// Type name for a logical CSD qubit.
pub const QUBIT_TYPENAME: TypeName = TypeName::new_inline("qubit");

/// Type of a single logical CSD qubit.
pub fn logical_qubit_type() -> Type {
    logical_qubit_type_with_extension(&Arc::downgrade(&EXTENSION))
}

/// Tuple of logical qubits in slots 0 and 1 of the same CSD block.
pub fn logical_qubit_pair_type() -> Type {
    Type::new_tuple(vec![logical_qubit_type(); 2])
}

// Use the supplied reference during extension initialization to avoid recursively
// initializing EXTENSION when operation signatures refer to the qubit type.
fn logical_qubit_type_with_extension(extension_ref: &Weak<Extension>) -> Type {
    CustomType::new(
        QUBIT_TYPENAME,
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
    /// Prepare a same-block pair of logical qubits in the zero state.
    prep_zero,
    /// Prepare a same-block pair of logical qubits in the T magic state T|+>.
    prep_magic_state,
    /// Prepare one logical qubit in the zero state, without allocating a partner wire.
    prep_zero_single,
    /// Destructively measure a qubit pair in Z, returning two booleans in slot order.
    measure_z,
    /// Destructively measure one logical qubit in Z, consuming it and returning a boolean.
    measure_z_single,
    /// Apply CNOT from each slot of the control pair to the matching slot of the target pair.
    /// Return the control pair followed by the target pair.
    transversal_cnot,
    /// Apply CNOT from the first logical qubit to the second, returning both in input order.
    targeted_cnot,
    /// Apply S to both qubits of a pair, returning the pair in slot order.
    global_s,
    /// Apply T to the data pair using the second (magic) pair, returning only the data pair.
    global_t,
    /// Apply T to the data qubit using slot 0 of the magic pair, consuming the entire pair.
    /// Discard the unused magic resource in slot 1 and return only the data qubit.
    targeted_t,
    /// Apply H to one logical qubit.
    targeted_h,
    /// Non-destructively measure one logical qubit in Z, returning the qubit and a boolean.
    targeted_measure_z,
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
        Ok(ConcreteCsdOp { def: *self })
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
        let qubit = logical_qubit_type_with_extension(extension_ref);
        let pair = Type::new_tuple(vec![qubit.clone(); 2]);
        match self {
            Self::prep_zero | Self::prep_magic_state => Signature::new(vec![], vec![pair]),
            Self::prep_zero_single => Signature::new(vec![], vec![qubit]),
            Self::global_s => Signature::new_endo(vec![pair]),
            Self::targeted_cnot => Signature::new_endo(vec![qubit; 2]),
            Self::targeted_h => Signature::new_endo(vec![qubit]),
            // Data inputs precede the magic inputs, which injection consumes.
            Self::global_t => Signature::new(vec![pair.clone(); 2], vec![pair]),
            Self::targeted_t => Signature::new(vec![qubit.clone(), pair], vec![qubit]),
            Self::transversal_cnot => Signature::new_endo(vec![pair; 2]),
            Self::measure_z => Signature::new(vec![pair], vec![bool_t(); 2]),
            Self::measure_z_single => Signature::new(vec![qubit], vec![bool_t()]),
            Self::targeted_measure_z => Signature::new(vec![qubit.clone()], vec![qubit, bool_t()]),
        }
        .into()
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for the logical CSD qubit type and operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        extension
            .add_type(
                QUBIT_TYPENAME,
                vec![],
                "logical CSD qubit".to_owned(),
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
        extension::prelude::{MakeTuple, UnpackTuple},
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
        assert_eq!(EXTENSION.operations().count(), 12);
        assert!(!logical_qubit_type().copyable());
        assert!(!logical_qubit_pair_type().copyable());
        assert_eq!(
            Type::new_extension(
                EXTENSION
                    .get_type(&QUBIT_TYPENAME)
                    .unwrap()
                    .instantiate([])
                    .unwrap()
            ),
            logical_qubit_type()
        );
    }

    #[test]
    fn test_signatures() {
        for (def, signature) in [
            (
                CsdOpDef::prep_zero_single,
                Signature::new(vec![], vec![logical_qubit_type()]),
            ),
            (
                CsdOpDef::measure_z_single,
                Signature::new(vec![logical_qubit_type()], vec![bool_t()]),
            ),
            (
                CsdOpDef::prep_zero,
                Signature::new(vec![], vec![logical_qubit_pair_type()]),
            ),
            (
                CsdOpDef::prep_magic_state,
                Signature::new(vec![], vec![logical_qubit_pair_type()]),
            ),
            (
                CsdOpDef::measure_z,
                Signature::new(vec![logical_qubit_pair_type()], vec![bool_t(); 2]),
            ),
            (
                CsdOpDef::transversal_cnot,
                Signature::new_endo(vec![logical_qubit_pair_type(); 2]),
            ),
            (
                CsdOpDef::global_s,
                Signature::new_endo(vec![logical_qubit_pair_type()]),
            ),
            (
                CsdOpDef::global_t,
                Signature::new(
                    vec![logical_qubit_pair_type(); 2],
                    vec![logical_qubit_pair_type()],
                ),
            ),
        ] {
            check_op(def, signature);
        }
    }

    #[test]
    fn test_targeted_signatures() {
        for (def, signature) in [
            (
                CsdOpDef::targeted_t,
                Signature::new(
                    vec![logical_qubit_type(), logical_qubit_pair_type()],
                    vec![logical_qubit_type()],
                ),
            ),
            (
                CsdOpDef::targeted_h,
                Signature::new_endo(vec![logical_qubit_type()]),
            ),
            (
                CsdOpDef::targeted_measure_z,
                Signature::new(
                    vec![logical_qubit_type()],
                    vec![logical_qubit_type(), bool_t()],
                ),
            ),
            (
                CsdOpDef::targeted_cnot,
                Signature::new_endo(vec![logical_qubit_type(); 2]),
            ),
        ] {
            check_op(def, signature);
        }
    }

    fn check_op(def: CsdOpDef, signature: Signature) {
        let op = def.instantiate_no_args().to_extension_op().unwrap();
        assert_eq!(op.signature().as_ref(), &signature);
        let restored = ConcreteCsdOp::from_extension_op(&op).unwrap();
        assert_eq!(restored.def, def);
        assert!(restored.type_args().is_empty());
        assert_eq!(
            EXTENSION
                .instantiate_extension_op(&def.opdef_id(), [])
                .unwrap()
                .signature()
                .as_ref(),
            &signature
        );
    }

    #[test]
    fn test_reject_type_arguments() {
        for def in CsdOpDef::iter() {
            for args in [
                vec![0.into()],
                vec![0.into(), 1.into()],
                vec![bool_t().into()],
            ] {
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
            module_builder.define_function("main", Signature::new(vec![], vec![bool_t(); 6]))?;
        let mut pairs = Vec::new();
        for _ in 0..2 {
            let [pair] = f_build
                .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_zero", [])?, [])?
                .outputs_arr();
            pairs.push(pair);
        }
        pairs = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("transversal_cnot", [])?,
                pairs,
            )?
            .outputs()
            .collect();
        [pairs[0]] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("global_s", [])?,
                [pairs[0]],
            )?
            .outputs_arr();
        let [magic_pair] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("prep_magic_state", [])?,
                [],
            )?
            .outputs_arr();
        [pairs[0]] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("global_t", [])?,
                [pairs[0], magic_pair],
            )?
            .outputs_arr();

        // Targeted gates use individual wires unpacked from the block pairs.
        let mut qubits = Vec::new();
        for pair in pairs {
            qubits.extend(
                f_build
                    .add_dataflow_op(
                        UnpackTuple::new(vec![logical_qubit_type(); 2].into()),
                        [pair],
                    )?
                    .outputs(),
            );
        }
        [qubits[0], qubits[2]] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("targeted_cnot", [])?,
                [qubits[0], qubits[2]],
            )?
            .outputs_arr();
        [qubits[0]] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("targeted_h", [])?,
                [qubits[0]],
            )?
            .outputs_arr();
        for qubit in &mut qubits[..2] {
            let [magic_pair] = f_build
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op("prep_magic_state", [])?,
                    [],
                )?
                .outputs_arr();
            [*qubit] = f_build
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op("targeted_t", [])?,
                    [*qubit, magic_pair],
                )?
                .outputs_arr();
        }
        let [qubit, measurement] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("targeted_measure_z", [])?,
                [qubits[0]],
            )?
            .outputs_arr();
        qubits[0] = qubit;
        let mut outputs = vec![measurement];
        // Reassemble the original block pairs before whole-block measurement.
        for qubit_pair in qubits.chunks_exact(2) {
            let [pair] = f_build
                .add_dataflow_op(
                    MakeTuple::new(vec![logical_qubit_type(); 2].into()),
                    qubit_pair.iter().copied(),
                )?
                .outputs_arr();
            let measurement = f_build
                .add_dataflow_op(EXTENSION.instantiate_extension_op("measure_z", [])?, [pair])?;
            outputs.extend(measurement.outputs());
        }
        let [data] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("prep_zero_single", [])?,
                [],
            )?
            .outputs_arr();
        let [magic] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("prep_magic_state", [])?,
                [],
            )?
            .outputs_arr();
        let [data] = f_build
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("targeted_t", [])?,
                [data, magic],
            )?
            .outputs_arr();
        outputs.extend(
            f_build
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op("measure_z_single", [])?,
                    [data],
                )?
                .outputs(),
        );
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
