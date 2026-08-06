use pyo3::PyResult;
use pyo3::exceptions::PyValueError;
use std::sync::Arc;
use tket::hugr::Extension;
use tket::hugr::extension::ExtensionRegistry;

pub fn lookup_ext<'a>(registry: &'a ExtensionRegistry, name: &str) -> PyResult<&'a Arc<Extension>> {
    registry
        .get(name)
        .ok_or_else(|| PyValueError::new_err(format!("Unknown extension: '{name}'")))
}
