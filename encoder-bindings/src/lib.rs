//! Supporting Rust library for the Python bindings.

mod hugr;

use pyo3::pymodule;
/// Python module containing the Rust bindings.
///
/// The definitions here should be reflected in the
/// `encoder/src/guppy_ft_encoder/_bindings/__init__.pyi` type stubs.
#[pymodule]
mod _bindings {
    #[pymodule_export]
    use crate::hugr::RsHugr;
    use encoder::encode;
    use pyo3::exceptions::PyValueError;
    use pyo3::prelude::*;
    use std::collections::BTreeMap;
    use tket::passes::ComposablePass;

    #[pyfunction]
    #[pyo3(signature = (rs_hugr, rewrite_ops))]
    fn _replace_ops(
        rs_hugr: &mut RsHugr,
        rewrite_ops: BTreeMap<(String, String), (RsHugr, String)>,
    ) -> PyResult<()> {
        let hugr = &mut rs_hugr.hugr;

        let new_ops = rewrite_ops
            .into_iter()
            .map(|(k, (rs_hugr, func_name))| (k, (rs_hugr.hugr, func_name)))
            .collect();

        let pass = encode::EncoderPass::new(new_ops);
        pass.run(hugr).map_err(|e| panic!("{:?}", e)).unwrap();
        pass.run(hugr)
            .map_err(|e| PyValueError::new_err(format!("Error replacing operations: {e}")))?;

        Ok(())
    }
}
