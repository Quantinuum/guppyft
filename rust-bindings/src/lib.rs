//! Supporting Rust library for the Python bindings.

mod hugr;
mod util;

use pyo3::pymodule;
/// Python module containing the Rust bindings.
///
/// The definitions here should be reflected in the `src/guppyft/_bindings/__init__.pyi` type stubs.
#[pymodule]
mod _bindings {
    #[pymodule_export]
    use crate::hugr::RsHugr;
    use crate::util::lookup_op;
    use guppyft::implement_ops;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use std::collections::{BTreeMap, HashSet};
    use tket::hugr::HugrView;
    use tket::passes::replace_types::NodeTemplate;
    use tket::passes::{ComposablePass, ReplaceTypes};

    /// A single [`hugr::types::TypeArg`] value as passed from Python, either an int
    /// (mapped to a `BoundedNat` argument) or a str (mapped to a `String` argument).
    #[derive(Debug, Clone, FromPyObject)]
    enum PyTypeArgValue {
        Int(u64),
        Str(String),
    }

    #[pyfunction]
    #[pyo3(signature = (rs_hugr, op_replacements, extensions=None))]
    fn _replace_encoder(
        rs_hugr: &mut RsHugr,
        op_replacements: BTreeMap<(String, String), (String, String, Vec<PyTypeArgValue>)>,
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
            let src = match lookup_op(&registry, src_ext, src_op, vec![]) {
                Ok(op) => op,
                Err(..) => continue,
            };
            let type_args: Vec<TypeArg> = tgt_args
                .iter()
                .map(|arg: &PyTypeArgValue| match arg {
                    PyTypeArgValue::Int(n) => TypeArg::from(*n),
                    PyTypeArgValue::Str(s) => TypeArg::from(s.clone()),
                })
                .collect();
            let tgt = lookup_op(&registry, tgt_ext, tgt_op, type_args)?;
            pass.set_replace_op(&src, NodeTemplate::SingleOp(tgt.into()));
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
            .map(|(ext_str, ty_str)| {
                let ext = hugr.extensions().get(ext_str).ok_or_else(|| {
                    PyValueError::new_err(format!(
                        "Unknown extension in ty_replacements: '{ext_str}'"
                    ))
                })?;

                let ty = ext.get_type(ty_str).ok_or_else(|| {
                    PyValueError::new_err(format!(
                        "Unknown type in ty_replacements: '{ext_str}.{ty_str}'"
                    ))
                })?;
                Ok((ty.extension_id().clone(), ty.name().clone()))
            })
            .collect::<PyResult<HashSet<_>>>()?;

        let pass = implement_ops::ImplementOpsPass::new(new_ops, ty_hashset);
        pass.run(hugr)
            .map_err(|e| PyValueError::new_err(format!("Error replacing operations: {e}")))?;

        Ok(())
    }
}
