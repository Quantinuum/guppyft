//! Extension providing standard ops for guppyft

use crate::std::types::logical_measurement_tv;
use documented::DocumentedVariants;
use hugr::Extension;
use hugr::extension::prelude::bool_t;
use hugr::extension::simple_op::{
    HasConcrete, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError, try_from_name,
};
use hugr::extension::{
    CustomValidator, ExtensionId, OpDef, SignatureError, SignatureFunc, ValidateJustArgs,
};
use hugr::ops::{ExtensionOp, OpName};
use hugr::types::type_param::{TermKindError, TypeParam};
use hugr::types::{FuncValueType, PolyFuncTypeRV, TypeArg, TypeBound, TypeRowRV};
use std::sync::{Arc, LazyLock, Weak};
use strum::{EnumIter, EnumString, IntoStaticStr};

/// Validates the type arguments of the `decode` op: `[k, row]` where `k` is
/// the receiver's `nat` size and `row` is a list of `k` `Bool` types (the
/// element types of the returned tuple's row variable). Unlike a
/// `SignatureFromArgs`/`CustomFunc` signature, this keeps the op's signature
/// as a plain, serializable `PolyFuncTypeRV` (with a row variable standing
/// in for the tuple's variable arity) -- the caller supplies the expanded
/// list of `k` `Bool`s explicitly as the second type argument, and this
/// validator merely checks consistency between the two arguments.
struct DecodeValidator;

impl ValidateJustArgs for DecodeValidator {
    fn validate(&self, arg_values: &[TypeArg]) -> Result<(), SignatureError> {
        let [k_arg, row_arg] = arg_values else {
            return Err(SignatureError::from(TermKindError::WrongNumberArgs(
                arg_values.len(),
                2,
            )));
        };
        // TypeArgs may be variable uses, in which case we can't extract
        // concrete values to cross-check, so just return Ok in that case.
        let Some(k) = k_arg.as_nat() else {
            return Ok(());
        };
        let TypeArg::List(row) = row_arg else {
            return Ok(());
        };
        if row.len() as u64 != k {
            return Err(SignatureError::InvalidTypeArgs);
        }
        let bool_arg: TypeArg = bool_t().into();
        if row.iter().any(|elem| *elem != bool_arg) {
            return Err(SignatureError::InvalidTypeArgs);
        }
        Ok(())
    }
}

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
    /// decode measurement.
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
            // The `decode` op takes two type params: `k` (nat), the size of
            // the receiver, and a row variable standing in for `k` `Bool`
            // types -- substituted at instantiation time with the concrete
            // list of `k` `Bool`s, expanding the output row to the right
            // arity. Note the row variable *is* the output row directly (not
            // wrapped in `Type::new_tuple`): Guppy compiles a custom op
            // returning a `TupleType` by unpacking it into that many
            // separate output ports (`type_to_row`), then re-packing them
            // into a runtime tuple value afterwards -- so the op itself must
            // expose `k` separate ports, matching that convention. This is a
            // plain, declarative `PolyFuncTypeRV` (row variable substitution
            // is a built-in HUGR mechanism), so unlike a
            // `SignatureFromArgs`-based signature it survives serialization
            // round-trips.
            decode => CustomValidator::new(
                PolyFuncTypeRV::new(
                    vec![
                        TypeParam::max_nat_kind(),
                        TypeParam::new_list_kind(TypeBound::Copyable),
                    ],
                    FuncValueType::new(
                        vec![logical_measurement_tv(0)],
                        TypeRowRV::new_var_use(1, TypeBound::Copyable),
                    ),
                ),
                DecodeValidator,
            )
            .into(),
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

#[derive(Debug)]
/// Concrete instantiations of operations in the `guppyft.std.ops` extension.
pub enum StdOp {
    Decode { k: TypeArg, row: TypeArg },
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
            Self::Decode { k, row } => {
                vec![k.clone(), row.clone()]
            }
        }
    }
}

impl HasConcrete for StdOpDef {
    type Concrete = StdOp;

    fn instantiate(&self, type_args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        match self {
            Self::decode => {
                let [k_arg, row_arg] = type_args else {
                    Err(SignatureError::from(TermKindError::WrongNumberArgs(
                        type_args.len(),
                        2,
                    )))?
                };

                Ok(StdOp::Decode {
                    k: k_arg.clone(),
                    row: row_arg.clone(),
                })
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

    fn bool_row_arg(k: usize) -> TypeArg {
        TypeArg::new_list(vec![bool_t(); k])
    }

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
                .instantiate(&[2.into(), bool_row_arg(2)])
                .unwrap()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([logical_measurement_type(2)], vec![bool_t(), bool_t()])
        );
    }

    #[test]
    fn test_signatures_rejects_mismatched_row() {
        assert!(
            StdOpDef::decode
                .instantiate(&[2.into(), bool_row_arg(3)])
                .unwrap()
                .to_extension_op()
                .is_err()
        );
    }

    #[test]
    fn test_hugr() {
        let decode = EXTENSION
            .instantiate_extension_op("decode", [2.into(), bool_row_arg(2)])
            .unwrap();

        let mut module_builder = ModuleBuilder::new();
        let mut foo = module_builder
            .define_function(
                "foo",
                Signature::new(vec![logical_measurement_type(2)], vec![bool_t(), bool_t()]),
            )
            .unwrap();
        let outs = foo.add_dataflow_op(decode, foo.input_wires()).unwrap();
        foo.finish_with_outputs(outs.outputs()).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }
}
