//! The implement pass for replacing operations with function implementations.

#![allow(missing_docs)]

use crate::implement_ops::{OpReplacementError, OpReplacer};
use hugr::hugr::ValidationError;
use hugr::ops::ExtensionOp;
use hugr::types::{CustomType, Type, TypeArg};
use hugr::{
    Hugr, HugrView, Node,
    builder::BuildError,
    extension::{ExtensionRegistry, SignatureError},
};
use hugr_core::extension::OpDef;
use hugr_core::extension::resolution::ExtensionResolutionError;
use hugr_core::hugr::internal::HugrMutInternals;
use std::collections::BTreeMap;
use std::sync::Arc;
use tket::extension::guppy::{DROP_OP_NAME, GUPPY_EXTENSION};
use tket::passes::ReplaceTypes;
use tket::passes::replace_types::handlers::register_linear_array_op_replacements;
use tket::passes::replace_types::{Linearizer, NodeTemplate};

pub type Linearizers = BTreeMap<(String, String), ((String, String), (String, String))>;

#[derive(derive_more::Error, Debug, derive_more::Display, derive_more::From)]
#[non_exhaustive]
pub enum ReplacementCompilerError {
    #[error(ignore)]
    #[display("Unknown extension: {_0}")]
    UnknownExtension(String),
    #[display("Could not instantiate extension op {}.{}: {_1}", _0.0, _0.1)]
    FailedOpInstantiation((String, String), SignatureError),
    #[display("Error getting {_0} ty: {_1}")]
    FailedTypeResolution(&'static str, String),
    #[from]
    OpReplacementError(OpReplacementError),
    #[from]
    ValidationError(ValidationError<Node>),
    #[display("Could not resolve extensions after replacing ops: {_0}")]
    PostResolveExtensionsError(ExtensionResolutionError),
    #[from(SignatureError, BuildError)]
    BuildError(BuildError),
    MissingFunctionHugr {
        name: String,
    },
}

#[derive(Debug, Clone, Default)]
pub struct ReplacementCompiler {
    op_replacements: BTreeMap<(String, String), (String, String, Vec<TypeArg>)>,
    compound_op_replacements: BTreeMap<(String, String), Hugr>,
    ty_replacements: BTreeMap<(String, String), (String, String)>,
    additional_extensions: Option<ExtensionRegistry>,
    linearizers: Linearizers,
}

fn get_type_from_registry(
    registry: &ExtensionRegistry,
    ext_name: &str,
    ty_name: &str,
) -> Result<Option<CustomType>, String> {
    let Some(ty_def) = registry.get(ext_name).and_then(|e| e.get_type(ty_name)) else {
        return Ok(None);
    };
    if !ty_def.params().is_empty() {
        return Err(format!(
            "Generic types are not supported for type replacement: '{ext_name}.{ty_name}'"
        ));
    }
    let ty = ty_def
        .instantiate([])
        .map_err(|e| format!("Could not instantiate ty: {e}"))?;
    Ok(Some(ty))
}

impl ReplacementCompiler {
    pub const fn new(
        op_replacements: BTreeMap<(String, String), (String, String, Vec<TypeArg>)>,
        compound_op_replacements: BTreeMap<(String, String), Hugr>,
        ty_replacements: BTreeMap<(String, String), (String, String)>,
        additional_extensions: Option<ExtensionRegistry>,
        linearizers: Linearizers,
    ) -> Self {
        Self {
            op_replacements,
            compound_op_replacements,
            ty_replacements,
            additional_extensions,
            linearizers,
        }
    }

    #[allow(unused)]
    pub(crate) fn run(self, hugr: &mut Hugr) -> anyhow::Result<()> {
        let registry = hugr.extensions_mut();
        if let Some(additional_extensions) = self.additional_extensions {
            registry.extend(additional_extensions);
        }

        let mut replacer = if self.linearizers.is_empty() {
            ReplaceTypes::new_empty()
        } else {
            let mut replacer = ReplaceTypes::default();
            register_linear_array_op_replacements(&mut replacer);
            // Guppy emits explicit drops for arrays and other affine values.
            // Expand them before the logical element type becomes a Cell pointer.
            replacer.set_replace_parametrized_op(
                GUPPY_EXTENSION.get_op(DROP_OP_NAME.as_str()).unwrap(),
                |args, rt| {
                    let [ty] = args else {
                        unreachable!("Guppy drop expects one type argument")
                    };
                    let ty = Type::try_from(ty.clone()).unwrap();
                    Ok(Some(rt.get_linearizer().copy_discard_op(&ty, 0)?))
                },
            );
            replacer
        };
        for ((ext, name), (copy, discard)) in self.linearizers {
            let ty = get_type_from_registry(registry, &ext, &name)
                .map_err(anyhow::Error::msg)?
                .ok_or_else(|| anyhow::anyhow!("Unknown linearizer type: {ext}.{name}"))?;
            let instantiate = |(ext, name): (String, String)| -> anyhow::Result<NodeTemplate> {
                let op = registry
                    .get(&ext)
                    .ok_or_else(|| ReplacementCompilerError::UnknownExtension(ext.clone()))?
                    .instantiate_extension_op(&name, [])?;
                Ok(NodeTemplate::SingleOp(op.into()))
            };
            replacer.linearizer_mut().register_simple(
                ty,
                instantiate(copy)?,
                instantiate(discard)?,
            )?;
        }
        for ((src_ext, src_op), (tgt_ext, tgt_op, tgt_args)) in self.op_replacements.into_iter() {
            let Some(src_def) = registry.get(&src_ext).and_then(|e| e.get_op(&src_op)) else {
                continue;
            };

            // Resolve the target extension eagerly, so a missing extension is
            // reported immediately rather than only once a matching node is
            // found during `pass.run`.
            let tgt = registry
                .get(&tgt_ext)
                .ok_or(ReplacementCompilerError::UnknownExtension(tgt_ext.clone()))?
                .instantiate_extension_op(&tgt_op, tgt_args)
                .map_err(|e| {
                    ReplacementCompilerError::FailedOpInstantiation((tgt_ext, tgt_op), e)
                })?;

            replacer.set_replace_parametrized_op(src_def, move |_, _| {
                Ok(Some(NodeTemplate::SingleOp(tgt.clone().into())))
            });
        }

        for ((src_ext_name, src_ty), (tgt_ext_name, tgt_ty)) in self.ty_replacements.into_iter() {
            let Some(src) = get_type_from_registry(registry, &src_ext_name, &src_ty)
                .map_err(|e| ReplacementCompilerError::FailedTypeResolution("src", e))?
            else {
                continue;
            };
            let Some(tgt) = get_type_from_registry(registry, &tgt_ext_name, &tgt_ty)
                .map_err(|e| ReplacementCompilerError::FailedTypeResolution("tgt", e))?
            else {
                continue;
            };

            replacer.set_replace_type(src, tgt.into());
        }

        // Resolve compound extensions before creating op replacer to avoid double mutable borrow
        // of the hugr variable.
        let compound_op_replacements: Vec<(Arc<OpDef>, Hugr)> = self
            .compound_op_replacements
            .into_iter()
            .filter_map(|((ext, op), replacement)| {
                registry
                    .get(&ext)
                    .and_then(|e| e.get_op(&op))
                    .map(|op_def| (op_def.clone(), replacement))
            })
            .collect();

        let mut op_replacer = OpReplacer::new(hugr, replacer);
        for (op_def, replacement) in compound_op_replacements.into_iter() {
            let func_name = replacement
                .entrypoint_optype()
                .as_func_defn()
                .unwrap()
                .func_name()
                .clone();
            assert!(op_def.params()?.is_empty());
            op_replacer.register_replacement(
                &ExtensionOp::new(op_def, [])?,
                Some(replacement),
                &func_name,
            )?;
        }
        op_replacer.finish()?;

        hugr.validate()?;
        Ok(())
    }
}
