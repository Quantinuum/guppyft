//! Supporting Rust module for the Python bindings.

mod hugr;

use pyo3::pymodule;
/// Python module containing the Rust bindings.
///
/// The definitions here should be reflected in the `src/guppyft/_bindings/__init__.pyi` type stubs.
#[pymodule]
mod _bindings {
    #[pymodule_export]
    use super::hugr::RsHugr;
    use crate::implement_ops;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use std::collections::{BTreeMap, HashSet};
    use tket::hugr::HugrView;
    use tket::hugr::extension::ExtensionRegistry;
    use tket::hugr::types::CustomType;
    use tket::passes::replace_types::NodeTemplate;
    use tket::passes::{ComposablePass, ReplaceTypes};

    /// A single [`hugr::types::TypeArg`] value as passed from Python, either an int
    /// (mapped to a `BoundedNat` argument) or a str (mapped to a `String` argument).
    #[derive(Debug, Clone, FromPyObject)]
    enum PyTypeArgValue {
        Int(u64),
        Str(String),
    }

    fn get_type_from_registry(
        registry: &ExtensionRegistry,
        ext_name: &str,
        ty_name: &str,
    ) -> Result<Option<CustomType>, String> {
        let ext = match registry.get(ext_name) {
            Some(e) => e,
            None => return Ok(None),
        };
        let Some(src_def) = ext.get_type(ty_name) else {
            return Ok(None);
        };
        if !src_def.params().is_empty() {
            return Err(format!(
                "Generic types are not supported for type replacement: '{ext_name}.{ty_name}'"
            ));
        }
        let src = src_def
            .instantiate([])
            .map_err(|e| format!("Could not instantiate src ty: {e}"))?;
        Ok(Some(src))
    }

    #[pyfunction]
    #[pyo3(signature = (rs_hugr, op_replacements, compound_op_replacements, ty_replacements, extensions=None))]
    fn _replacement_compiler_impl(
        rs_hugr: &mut RsHugr,
        op_replacements: BTreeMap<(String, String), (String, String, Vec<PyTypeArgValue>)>,
        compound_op_replacements: BTreeMap<(String, String), RsHugr>,
        ty_replacements: BTreeMap<(String, String), (String, String)>,
        extensions: Option<String>,
    ) -> PyResult<()> {
        use tket::hugr::extension::ExtensionRegistry;
        use tket::hugr::types::TypeArg;

        let hugr = &mut rs_hugr.hugr;

        // Build a registry extending the hugr extensions with any additional extensions provided.
        let mut registry: ExtensionRegistry = hugr.extensions().clone();
        if let Some(extensions_json) = extensions {
            let additional = ExtensionRegistry::load_json(extensions_json.as_bytes(), &registry)
                .map_err(|e| {
                    PyValueError::new_err(format!("Could not load additional extensions: {e}"))
                })?;
            registry.extend(additional);
        }

        let mut pass = ReplaceTypes::new_empty();

        for ((src_ext, src_op), (tgt_ext, tgt_op, tgt_args)) in op_replacements.iter() {
            let ext = match registry.get(src_ext) {
                Some(e) => e,
                None => continue,
            };
            let Some(src_def) = ext.get_op(src_op) else {
                continue;
            };

            // Resolve the target extension eagerly, so a missing extension is
            // reported immediately rather than only once a matching node is
            // found during `pass.run`.
            let tgt_ext = registry
                .get(tgt_ext)
                .ok_or_else(|| PyValueError::new_err(format!("Unknown extension: '{tgt_ext}'")))?
                .clone();
            let tgt_args: Vec<TypeArg> = tgt_args
                .iter()
                .map(|arg| match arg {
                    PyTypeArgValue::Int(n) => TypeArg::from(*n),
                    PyTypeArgValue::Str(s) => TypeArg::from(s.clone()),
                })
                .collect();
            let tgt = tgt_ext
                .instantiate_extension_op(tgt_op, tgt_args.clone())
                .map_err(|e| {
                    PyValueError::new_err(format!("Could not instantiate extension op: {e}"))
                })?;

            pass.set_replace_parametrized_op(src_def, move |_, _| {
                Ok(Some(NodeTemplate::SingleOp(tgt.clone().into())))
            });
        }

        for ((src_ext, src_op), replacement_hugr) in compound_op_replacements.into_iter() {
            let Some(src_def) = registry.get(&src_ext).and_then(|e| e.get_op(&src_op)) else {
                continue;
            };
            let node_template = NodeTemplate::call_to_function(replacement_hugr.hugr, &[])
                .map_err(|e| PyValueError::new_err(format!("Error {e}")))?;
            pass.set_replace_parametrized_op(src_def, move |_, _| Ok(Some(node_template.clone())));
        }

        for ((src_ext_name, src_ty), (tgt_ext_name, tgt_ty)) in ty_replacements.into_iter() {
            let Some(src) = get_type_from_registry(&registry, &src_ext_name, &src_ty)
                .map_err(|e| PyValueError::new_err(format!("Error getting src ty: {e}")))?
            else {
                continue;
            };
            let Some(tgt) = get_type_from_registry(&registry, &tgt_ext_name, &tgt_ty)
                .map_err(|e| PyValueError::new_err(format!("Error getting tgt ty: {e}")))?
            else {
                continue;
            };

            pass.set_replace_type(src, tgt.into());
        }

        pass.run(hugr)
            .map_err(|e| PyValueError::new_err(format!("Error encoding operations: {e}")))?;

        // `ReplaceTypes` swaps in ops/types from `registry` but does not update
        // the Hugr extension registry (`hugr.extensions()`), which is what
        // gets used when serializing. Without this, the newly-introduced ops/types
        // are written out as unresolved  `Custom` nodes, and the envelope doesn't
        // declare the new extensions as dependencies, so downstream consumers
        // can't resolve them.
        // The following updates `hugr.extensions()`, solving this issue.
        hugr.resolve_extension_defs(&registry).map_err(|e| {
            PyValueError::new_err(format!("Could not resolve extensions after encoding: {e}"))
        })?;

        hugr.validate()
            .map_err(|e| PyValueError::new_err(format!("Encoded Hugr failed validation: {e}")))?;

        Ok(())
    }

    #[pyfunction]
    fn _implement_ops(
        rs_hugr: &mut RsHugr,
        op_replacements: BTreeMap<(String, String), (Option<RsHugr>, String)>,
        replaceable_types: HashSet<(String, String)>,
    ) -> PyResult<()> {
        let hugr = &mut rs_hugr.hugr;

        let new_ops = op_replacements
            .into_iter()
            .map(|(k, (rs_hugr, func_name))| (k, (rs_hugr.map(|x| x.hugr), func_name)))
            .collect();

        let ty_hashset = replaceable_types
            .iter()
            .filter_map(|(ext_str, ty_str)| {
                let ext = hugr.extensions().get(ext_str)?;
                let ty = ext.get_type(ty_str).ok_or_else(|| {
                    PyValueError::new_err(format!(
                        "Unknown type in ty_replacements: '{ext_str}.{ty_str}'"
                    ))
                });
                Some(ty.map(|ty| (ty.extension_id().clone(), ty.name().clone())))
            })
            .collect::<PyResult<HashSet<_>>>()?;

        let pass = implement_ops::ImplementOpsPass::new(new_ops, ty_hashset);
        pass.run(hugr)
            .map_err(|e| PyValueError::new_err(format!("Error replacing operations: {e}")))?;

        Ok(())
    }
}
