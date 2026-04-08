//! Bindings for a rust-backed representation of a Hugr.
//!
//! Note: The code here will eventually be moved to the `tket` crate.

use std::num::NonZeroU8;

use pyo3::exceptions::{PyAttributeError, PyValueError};
use pyo3::types::PyAnyMethods;
use pyo3::{pyclass, pymethods, Bound, PyAny, PyErr, PyResult};
use tket::hugr::envelope::{EnvelopeFormat, ZstdConfig};
use tket::hugr::HugrView;
use tket::serialize::EnvelopeConfig;
use tket::Hugr;

/// A python object backed by rust `Hugr`.
#[pyclass(from_py_object)]
#[derive(Clone, Debug, PartialEq, derive_more::From)]
pub struct RsHugr {
    /// Rust representation of the hugr.
    pub hugr: Hugr,
}

#[pymethods]
impl RsHugr {
    /// Encode the hugr as a HUGR envelope.
    ///
    /// If no config is given, it defaults to the default binary envelope.
    #[pyo3(signature = (config = None))]
    pub fn to_bytes(&self, config: Option<Bound<'_, PyAny>>) -> PyResult<Vec<u8>> {
        let config = match config {
            Some(cfg) => envelope_config_from_py(cfg)?,
            None => EnvelopeConfig::binary(),
        };
        let mut buf = Vec::new();
        self.hugr
            .store_with_exts(&mut buf, config, self.hugr.extensions())
            .map_err(|e| PyErr::new::<PyValueError, _>(format!("Could not encode hugr: {e}")))?;
        Ok(buf)
    }

    /// Encode the circuit as a HUGR envelope.
    ///
    /// If no config is given, it defaults to the default text envelope.
    #[pyo3(signature = (config = None))]
    pub fn to_str(&self, config: Option<Bound<'_, PyAny>>) -> PyResult<String> {
        let config = match config {
            Some(cfg) => envelope_config_from_py(cfg)?,
            None => EnvelopeConfig::text(),
        };
        self.hugr
            .store_str_with_exts(config, self.hugr.extensions())
            .map_err(|e| PyErr::new::<PyAttributeError, _>(format!("Could not encode hugr: {e}")))
    }

    /// Loads a hugr from a HUGR envelope.
    ///
    /// If the name is not given, uses the encoded entrypoint.
    #[staticmethod]
    #[pyo3(signature = (bytes))]
    pub fn from_bytes(bytes: &[u8]) -> PyResult<Self> {
        let hugr = Hugr::load(bytes, None).map_err(|e| {
            PyErr::new::<PyAttributeError, _>(format!("Could not read envelope: {e}"))
        })?;
        Ok(RsHugr { hugr })
    }

    /// Loads a circuit from a HUGR envelope string.
    ///
    /// If the name is not given, uses the encoded entrypoint.
    #[staticmethod]
    #[pyo3(signature = (envelope))]
    pub fn from_str(envelope: &str) -> PyResult<Self> {
        let hugr = Hugr::load_str(envelope, None).map_err(|e| {
            PyErr::new::<PyAttributeError, _>(format!("Could not read envelope: {e}"))
        })?;
        Ok(RsHugr { hugr })
    }

    /// Copy the circuit.
    pub fn __copy__(&self) -> PyResult<Self> {
        Ok(self.clone())
    }

    /// Copy the circuit.
    pub fn __deepcopy__(&self, _memo: Bound<PyAny>) -> PyResult<Self> {
        Ok(self.clone())
    }

    fn render_mermaid(&self) -> String {
        self.hugr.mermaid_string()
    }
}

/// Converts a python `hugr.envelope.EnvelopeConfig` into a rust-based [`EnvelopeConfig`].
pub fn envelope_config_from_py(config: Bound<'_, PyAny>) -> PyResult<EnvelopeConfig> {
    let mut res = EnvelopeConfig::default();

    let format = config.getattr("format")?;
    let format_ident: usize = format.getattr("value")?.extract()?;
    res.format = EnvelopeFormat::from_repr(format_ident).ok_or_else(|| {
        PyErr::new::<PyValueError, _>(format!("Invalid envelope format: {format_ident}"))
    })?;

    let zstd: Option<usize> = config.getattr("zstd")?.extract()?;
    res.zstd = zstd.map(|level| {
        let mut z = ZstdConfig::default();
        // Compression level 0 means default compression.
        // We represent that as `None` on the rust struct.
        if level > 0 && level < u8::MAX as usize {
            z.level = Some(NonZeroU8::new(level as u8).unwrap());
        }
        z
    });

    Ok(res)
}
