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
    use crate::{implement_ops, replacement};
    use itertools::Itertools as _;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use std::collections::{BTreeMap, HashSet};
    use tket::hugr::HugrView;
    use tket::hugr::extension::ExtensionRegistry;
    use tket::hugr::types::TypeArg;
    use tket::passes::ComposablePass;

    /// A single [`hugr::types::TypeArg`] value as passed from Python, either an int
    /// (mapped to a `BoundedNat` argument) or a str (mapped to a `String` argument).
    #[derive(Debug, Clone, FromPyObject)]
    enum PyTypeArgValue {
        Int(u64),
        Str(String),
    }

    impl From<PyTypeArgValue> for TypeArg {
        fn from(value: PyTypeArgValue) -> Self {
            match value {
                PyTypeArgValue::Int(n) => TypeArg::from(n),
                PyTypeArgValue::Str(s) => TypeArg::from(s),
            }
        }
    }

    #[pyfunction]
    #[pyo3(signature = (rs_hugr, op_replacements, compound_op_replacements, ty_replacements, extensions=None))]
    fn _run_replacement_compiler(
        rs_hugr: &mut RsHugr,
        op_replacements: BTreeMap<(String, String), (String, String, Vec<PyTypeArgValue>)>,
        compound_op_replacements: BTreeMap<(String, String), RsHugr>,
        ty_replacements: BTreeMap<(String, String), (String, String)>,
        extensions: Option<String>,
    ) -> PyResult<()> {
        let op_replacements = op_replacements
            .into_iter()
            .map(|(key, (tgt_ext, tgt_op, tgt_args))| {
                let tgt_args: Vec<TypeArg> = tgt_args.into_iter().map_into().collect();
                (key, (tgt_ext, tgt_op, tgt_args))
            })
            .collect();

        let compound_op_replacements = compound_op_replacements
            .into_iter()
            .map(|(key, rs_hugr)| (key, rs_hugr.hugr))
            .collect();

        let hugr = &mut rs_hugr.hugr;
        let extensions = match extensions {
            Some(json) => Some(
                ExtensionRegistry::load_json(json.as_bytes(), hugr.extensions()).map_err(|e| {
                    PyValueError::new_err(format!("Could not load additional extensions: {e}"))
                })?,
            ),
            None => None,
        };

        let compiler = replacement::ReplacementCompiler::new(
            op_replacements,
            compound_op_replacements,
            ty_replacements,
            extensions,
        );
        compiler.run(hugr).map_err(|e| {
            PyValueError::new_err(format!("Error running replacement compiler: {e}"))
        })?;

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
