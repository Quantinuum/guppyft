//! Extension providing standard ops for guppyft

use crate::std::types::logical_measurement_type;
use documented::DocumentedVariants;
use hugr::Extension;
use hugr::extension::prelude::bool_t;
use hugr::extension::simple_op::{
    HasConcrete, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError, try_from_name,
};
use hugr::extension::{ExtensionId, OpDef, SignatureError, SignatureFromArgs, SignatureFunc};
use hugr::ops::{ExtensionOp, OpName};
use hugr::types::type_param::{TermKindError, TypeParam};
use hugr::types::{FuncValueType, PolyFuncTypeRV, TypeArg};
use std::sync::{Arc, LazyLock, Weak};
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.std.ops");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum StdOpDef {
    /// decode measurement
    decode,
}

impl MakeOpDef for StdOpDef {
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
        use StdOpDef::*;
        match self {
            decode => (*self).into(),
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Static parameter for decode op
const STATIC_NAT_PARAM: &[TypeParam; 1] = &[TypeParam::max_nat_kind()];

impl SignatureFromArgs for StdOpDef {
    fn compute_signature(&self, arg_values: &[TypeArg]) -> Result<PolyFuncTypeRV, SignatureError> {
        let [TypeArg::BoundedNat(n)] = *arg_values else {
            return Err(SignatureError::InvalidTypeArgs);
        };
        let sig = match self {
            StdOpDef::decode => PolyFuncTypeRV::new(
                vec![],
                FuncValueType::new(
                    vec![logical_measurement_type(n)],
                    vec![bool_t(); n as usize],
                ),
            ),
        };
        Ok(sig)
    }

    fn static_params(&self) -> &[TypeParam] {
        STATIC_NAT_PARAM
    }
}

#[derive(Debug)]
/// Concrete instantiations of operations in the `guppyft.std.ops` extension.
pub enum StdOp {
    Decode { k: TypeArg },
}

impl MakeExtensionOp for StdOp {
    fn op_id(&self) -> OpName {
        match self {
            Self::Decode { .. } => StdOpDef::decode.opdef_id(),
        }
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError>
    where
        Self: Sized,
    {
        StdOpDef::from_def(ext_op.def())?.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        match self {
            Self::Decode { k } => {
                vec![k.clone()]
            }
        }
    }
}

impl HasConcrete for StdOpDef {
    type Concrete = StdOp;

    fn instantiate(&self, type_args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        match self {
            Self::decode => {
                let [k_arg] = type_args else {
                    Err(SignatureError::from(TermKindError::WrongNumberArgs(
                        type_args.len(),
                        1,
                    )))?
                };

                Ok(StdOp::Decode { k: k_arg.clone() })
            }
        }
    }
}

impl MakeRegisteredOp for StdOp {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

/// Extension for guppyft.std operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        StdOpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::std::types::logical_measurement_type;
    use hugr::HugrView;
    use hugr::builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder};
    use hugr::ops::DataflowOpTrait;
    use hugr::types::Signature;

    #[test]
    fn test_std_ops_extension() {
        assert_eq!(EXTENSION.name().to_string(), "guppyft.std.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 1);
    }

    #[test]
    fn test_signatures() {
        assert_eq!(
            StdOpDef::decode
                .instantiate(&[2.into()])
                .unwrap()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([logical_measurement_type(2)], vec![bool_t(); 2])
        );
    }

    #[test]
    fn test_hugr() {
        let decode = EXTENSION
            .instantiate_extension_op("decode", [2.into()])
            .unwrap();

        let mut module_builder = ModuleBuilder::new();
        let mut foo = module_builder
            .define_function(
                "foo",
                Signature::new(vec![logical_measurement_type(2)], vec![bool_t(); 2]),
            )
            .unwrap();
        let outs = foo.add_dataflow_op(decode, foo.input_wires()).unwrap();
        foo.finish_with_outputs(outs.outputs()).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
