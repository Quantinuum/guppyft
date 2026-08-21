use crate::c4::types::{logical_block_type, logical_measurement_type};
use documented::DocumentedVariants;
use hugr::Extension;
use hugr::extension::prelude::bool_t;
use hugr::extension::simple_op::{
    HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError, try_from_name,
};
use hugr::extension::{ExtensionId, OpDef, SignatureFunc};
use hugr::ops::{ExtensionOp, OpName};
use hugr::types::{FuncValueType, TypeArg};
use std::sync::{Arc, LazyLock, Weak};
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.c4.ops");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Logical C4 operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum C4OpDef {
    /// Prepare a C4 block in the all-zero logical state.
    prep_all_zero,
    /// Destructively measure a C4 block in the Z basis
    measure_all,
    /// Decode a measurement on a C4 block
    decode,
    /// Free a logical C4 block
    free,
}

/// Concrete C4 logical operation.
pub struct ConcreteC4Op {
    /// The kind of operation.
    pub def: C4OpDef,
}

impl HasConcrete for C4OpDef {
    type Concrete = ConcreteC4Op;

    fn instantiate(&self, _args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        Ok(ConcreteC4Op { def: *self })
    }
}

impl HasDef for ConcreteC4Op {
    type Def = C4OpDef;
}

impl MakeExtensionOp for ConcreteC4Op {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        let def = C4OpDef::from_def(ext_op.def())?;
        def.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        vec![]
    }
}

impl MakeRegisteredOp for ConcreteC4Op {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl C4OpDef {
    /// Initialise a [`ConcreteC4Op`] from a [`C4OpDef`].
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteC4Op {
        ConcreteC4Op { def: self }
    }
}

impl MakeOpDef for C4OpDef {
    fn opdef_id(&self) -> OpName {
        <&Self as Into<&'static str>>::into(self).into()
    }

    fn from_def(op_def: &OpDef) -> Result<Self, OpLoadError> {
        try_from_name(op_def.name(), op_def.extension_id())
    }

    fn extension(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Weak<Extension> {
        Arc::downgrade(&EXTENSION)
    }

    fn init_signature(&self, _extension_ref: &Weak<Extension>) -> SignatureFunc {
        use C4OpDef::*;
        match self {
            prep_all_zero => FuncValueType::new(vec![], vec![logical_block_type()]).into(),
            measure_all => {
                FuncValueType::new(vec![logical_block_type()], vec![logical_measurement_type()])
                    .into()
            }
            decode => FuncValueType::new(vec![logical_measurement_type()], vec![bool_t()]).into(),
            free => FuncValueType::new(vec![logical_block_type()], vec![]).into(),
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for logical C4 operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        C4OpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::c4::types::EXTENSION as types_extension;
    use hugr::HugrView;
    use hugr::builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder};
    use hugr::envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope};
    use hugr::extension::ExtensionRegistry;
    use hugr::ops::DataflowOpTrait;
    use hugr::package::Package;
    use hugr::std_extensions::std_reg;
    use hugr::types::Signature;
    use std::error::Error;

    #[test]
    fn test_c4_ops_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.c4.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 4);
    }

    #[test]
    fn test_signatures() {
        assert_eq!(
            C4OpDef::prep_all_zero
                .instantiate_no_args()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([], [logical_block_type()])
        );
    }

    #[test]
    fn test_prep_free_measure_decode() -> Result<(), Box<dyn Error>> {
        let prep_all_zero = EXTENSION.instantiate_extension_op("prep_all_zero", [])?;
        let free = EXTENSION.instantiate_extension_op("free", [])?;
        let measure_all = EXTENSION.instantiate_extension_op("measure_all", [])?;
        let decode = EXTENSION.instantiate_extension_op("decode", [])?;

        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(vec![logical_block_type()], vec![bool_t()]);
        let mut f_build = module_builder.define_function("main", signature)?;

        let handle = f_build.add_dataflow_op(free, f_build.input_wires())?;
        assert_eq!(handle.outputs().count(), 0);

        let handle = f_build.add_dataflow_op(prep_all_zero.clone(), vec![])?;
        let handle = f_build.add_dataflow_op(measure_all, handle.outputs())?;
        let [bool_wire] = f_build
            .add_dataflow_op(decode, handle.outputs())?
            .outputs_arr();

        f_build.finish_with_outputs([bool_wire])?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_serialization() {
        let block = logical_block_type();
        let measurement = logical_measurement_type();
        let measure_all = EXTENSION
            .instantiate_extension_op("measure_all", [])
            .unwrap();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(vec![block], vec![measurement]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(measure_all, [0]).unwrap();
        let outs = linear.finish();
        f_build.finish_with_outputs(outs).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        let package = Package::new([h]);
        let mut bytes: Vec<u8> = Vec::new();
        write_envelope(
            &mut bytes,
            &package,
            EnvelopeConfig::new(EnvelopeFormat::ModelWithExtensions),
        )
        .unwrap();
        let buff = std::io::BufReader::new(bytes.as_slice());
        let mut reg: ExtensionRegistry = std_reg();
        reg.extend([types_extension.clone(), EXTENSION.clone()]);
        let (_, package1) = read_envelope(buff, &reg).unwrap();
        let h1 = &package1.modules[0];
        h1.validate().unwrap();
    }
}
