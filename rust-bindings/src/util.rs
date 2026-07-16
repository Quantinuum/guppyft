use pyo3::PyResult;
use pyo3::exceptions::PyValueError;
use std::sync::Arc;
use tket::hugr::Extension;
use tket::hugr::extension::ExtensionRegistry;
use tket::hugr::ops::ExtensionOp;
use tket::hugr::types::TypeArg;

pub fn lookup_ext<'a>(registry: &'a ExtensionRegistry, name: &str) -> PyResult<&'a Arc<Extension>> {
    registry
        .get(name)
        .ok_or_else(|| PyValueError::new_err(format!("Unknown extension: '{name}'")))
}

pub fn lookup_op(
    registry: &ExtensionRegistry,
    ext_name: &str,
    op_name: &str,
    args: Vec<TypeArg>,
) -> PyResult<ExtensionOp> {
    let ext = lookup_ext(registry, ext_name)?;
    ext.instantiate_extension_op(op_name, args.clone())
        .map_err(|e| {
            PyValueError::new_err(format!(
                "Could not instantiate op '{ext_name}.{op_name}' with args {args:?}: {e}"
            ))
        })
}
