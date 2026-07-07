//! Supporting Rust library for the Python bindings.

mod hugr;

use pyo3::pymodule;
/// Python module containing the Rust bindings.
///
/// The definitions here should be reflected in the `src/guppyft/_bindings/__init__.pyi` type stubs.
#[pymodule]
mod _bindings {
    #[pymodule_export]
    use crate::hugr::RsHugr;
    use guppyft::implement_ops;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use std::collections::{BTreeMap, HashSet};
    use tket::hugr::HugrView;
    use tket::passes::ComposablePass;

    #[pyfunction]
    fn _implement_ops(
        rs_hugr: &mut RsHugr,
        op_replacements: BTreeMap<(String, String), (Option<RsHugr>, String)>,
        ty_replacements: HashSet<(String, String)>,
    ) -> PyResult<()> {
        let hugr = &mut rs_hugr.hugr;

        let new_ops = op_replacements
            .into_iter()
            .map(|(k, (rs_hugr, func_name))| (k, (rs_hugr.map(|x| x.hugr), func_name)))
            .collect();

        let ty_hashset = ty_replacements
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
