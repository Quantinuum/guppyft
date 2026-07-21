//! HUGR extension for logical operations on the
//! [Steane code](https://arxiv.org/abs/quant-ph/9601029).
//!
//! The extension `guppyft.steane.types` provides one new type: the code block for the
//! Steane code, herein named a 'logical qubit', as a linear (non-copyable) type.
//!
//! ```
//! use extensions::steane::types::logical_qubit_type;
//!
//! let qubit = logical_qubit_type();
//! assert!(!qubit.copyable());
//! ```
//!
//! The extension `guppyft.steane.ops` provides operations that act on this qubit type.
//!
//! To allocate a new qubit initialized to zero, use a `prep_zero` operation:
//!
//! ```
//! use extensions::steane::ops::EXTENSION;
//!
//! let prep_zero = EXTENSION
//!     .instantiate_extension_op("prep_zero", [])
//!     .unwrap();
//! ```
//!
//! Use the `free` operation to free a previously allocated qubit.

pub mod ops;
pub mod types;
