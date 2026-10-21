//! Extension providing logical operations on C4-Helix codeblocks.
//!
//! Gates (and T/Tdg injection) have ideal logical semantics, including any
//! required Pauli-frame corrections. Addressable operations take runtime
//! logical indices (0 or 1); invalid indices cause a runtime panic.
use std::sync::{Arc, LazyLock, Weak};

use documented::DocumentedVariants;
use hugr::{
    Extension,
    extension::{
        ExtensionId, OpDef, SignatureError, SignatureFunc,
        simple_op::{
            HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError,
            try_from_name,
        },
    },
    ops::{ExtensionOp, OpName},
    std_extensions::arithmetic::int_types::int_type,
    types::{Signature, TypeArg},
};

use super::types::{block_type, t_state_type};
use crate::std::types::logical_measurement_type;
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.helix.ops");

/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Logical Helix operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum HelixOpDef {
    /// Prepare the all-zero state on a block.
    alloc_zero,
    /// Prepare the |++> state on a block.
    alloc_plus,
    /// Discard a block.
    free,
    /// Apply X to the logical qubit selected by a runtime index.
    x,
    /// Apply Y to the logical qubit selected by a runtime index.
    y,
    /// Apply Z to the logical qubit selected by a runtime index.
    z,
    /// Swap the two qubits in the block.
    swap,
    /// CX from logical qubit 0 to 1.
    cx,
    /// Hadamard on each logical qubit.
    h_all,
    /// Logical CZ.
    cz,
    /// Logical S on both qubits.
    ss,
    /// Targeted CX from the first block to the second.
    /// Runtime indices select the control and target; the other qubits are unchanged.
    cx_between_blocks,
    /// Apply CX from each logical qubit in the first block to the corresponding
    /// logical qubit in the second block.
    cx_transversal,
    /// Destructively measure both logical qubits in the X basis.
    measure_xx,
    /// Destructively measure both logical qubits in the Z basis.
    measure_zz,
    /// Perform syndrome extraction and recovery (or a Pauli-frame update).
    /// Ideally preserves the logical state, including external entanglement.
    qec_cycle,
    /// Create a resource that can be consumed to apply T or Tdg gates.
    prep_t_state,
    /// Consume a T-state resource and apply a T gate to the logical qubit
    /// selected by a runtime index.
    inject_t,
    /// Consume a T-state resource and apply a Tdg gate to the logical qubit
    /// selected by a runtime index.
    inject_tdg,
    /// Discard an unused T-state resource.
    free_t_state,
}

/// Concrete Helix logical operation.
pub struct ConcreteHelixOp {
    /// The kind of operation.
    pub def: HelixOpDef,
}

impl HasConcrete for HelixOpDef {
    type Concrete = ConcreteHelixOp;

    fn instantiate(&self, args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        if !args.is_empty() {
            return Err(SignatureError::InvalidTypeArgs.into());
        }
        Ok(ConcreteHelixOp { def: *self })
    }
}

impl HasDef for ConcreteHelixOp {
    type Def = HelixOpDef;
}

impl MakeExtensionOp for ConcreteHelixOp {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        let def = HelixOpDef::from_def(ext_op.def())?;
        def.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        vec![]
    }
}

impl MakeRegisteredOp for ConcreteHelixOp {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl HelixOpDef {
    /// Initialize an operation without static arguments.
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteHelixOp {
        ConcreteHelixOp { def: self }
    }
}

/// Signature with block inputs followed by runtime logical indices.
fn sig_blocks(n_in: usize, n_out: usize, n_indices: usize) -> SignatureFunc {
    let mut inputs = vec![block_type(); n_in];
    inputs.extend(vec![int_type(6); n_indices]);
    Signature::new(inputs, vec![block_type(); n_out]).into()
}

impl MakeOpDef for HelixOpDef {
    fn opdef_id(&self) -> OpName {
        <&Self as Into<&'static str>>::into(self).into()
    }

    fn from_def(op_def: &OpDef) -> Result<Self, OpLoadError> {
        try_from_name(op_def.name(), op_def.extension_id())
    }

    fn extension(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Weak<Extension> {
        Arc::downgrade(&EXTENSION)
    }

    fn init_signature(&self, _extension_ref: &Weak<Extension>) -> SignatureFunc {
        use HelixOpDef::*;
        match self {
            prep_t_state => Signature::new(vec![], [t_state_type()]).into(),
            free_t_state => Signature::new([t_state_type()], vec![]).into(),
            inject_t | inject_tdg => {
                Signature::new([block_type(), int_type(6), t_state_type()], [block_type()]).into()
            }
            alloc_zero | alloc_plus => sig_blocks(0, 1, 0),
            free => sig_blocks(1, 0, 0),
            x | y | z => sig_blocks(1, 1, 1),
            swap | cx | h_all | cz | ss | qec_cycle => sig_blocks(1, 1, 0),
            cx_between_blocks => sig_blocks(2, 2, 2),
            cx_transversal => sig_blocks(2, 2, 0),
            measure_xx | measure_zz => {
                Signature::new([block_type()], [logical_measurement_type(2)]).into()
            }
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for logical Helix operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        HelixOpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::helix::types::EXTENSION as types_extension;
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope},
        extension::{ExtensionRegistry, prelude::bool_t},
        ops::{DataflowOpTrait, Value},
        package::Package,
        std_extensions::{
            arithmetic::int_types::ConstInt,
            collections::{array::ArrayKind, borrow_array::BorrowArray},
            std_reg,
        },
    };
    use std::error::Error;
    use strum::IntoEnumIterator;

    #[test]
    fn test_helix_ops_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.helix.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 20);
    }

    #[test]
    fn test_signatures() -> Result<(), Box<dyn Error>> {
        let block = block_type();
        let index = int_type(6);
        for name in ["x", "y", "z"] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &Signature::new([block.clone(), index.clone()], [block.clone()])
            );
        }
        assert_eq!(
            EXTENSION
                .instantiate_extension_op("cx_between_blocks", [])?
                .signature()
                .as_ref(),
            &Signature::new(
                [block.clone(), block.clone(), index.clone(), index],
                [block.clone(), block.clone()]
            )
        );
        for name in ["measure_xx", "measure_zz"] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &Signature::new([block.clone()], [logical_measurement_type(2)])
            );
        }
        Ok(())
    }

    #[test]
    fn test_magic_state_lifecycle() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function("magic", Signature::new_endo([block_type()]))?;
        let [mut block] = function.input_wires_arr();
        let zero = function.add_load_const(Value::extension(ConstInt::new_u(6, 0)?));
        let one = function.add_load_const(Value::extension(ConstInt::new_u(6, 1)?));
        for (name, index) in [("inject_t", zero), ("inject_tdg", one)] {
            let [resource] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_t_state", [])?, [])?
                .outputs_arr();
            [block] = function
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op(name, [])?,
                    [block, index, resource],
                )?
                .outputs_arr();
        }
        let [unused] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_t_state", [])?, [])?
            .outputs_arr();
        function.add_dataflow_op(
            EXTENSION.instantiate_extension_op("free_t_state", [])?,
            [unused],
        )?;
        function.finish_with_outputs([block])?;
        module.finish_hugr()?.validate()?;
        Ok(())
    }

    #[test]
    fn test_magic_state_signatures() -> Result<(), Box<dyn Error>> {
        for (name, expected) in [
            ("prep_t_state", Signature::new(vec![], [t_state_type()])),
            ("free_t_state", Signature::new([t_state_type()], vec![])),
            (
                "inject_t",
                Signature::new([block_type(), int_type(6), t_state_type()], [block_type()]),
            ),
            (
                "inject_tdg",
                Signature::new([block_type(), int_type(6), t_state_type()], [block_type()]),
            ),
        ] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &expected
            );
        }
        Ok(())
    }

    #[test]
    fn test_magic_state_cannot_be_reused() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function("bad", Signature::new(vec![], vec![]))?;
        let [resource] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_t_state", [])?, [])?
            .outputs_arr();
        let free = EXTENSION.instantiate_extension_op("free_t_state", [])?;
        function.add_dataflow_op(free.clone(), [resource])?;
        assert!(function.add_dataflow_op(free, [resource]).is_err());
        Ok(())
    }

    #[test]
    fn test_injection_rejects_block_resource() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function(
            "bad",
            Signature::new([block_type(), int_type(6), block_type()], [block_type()]),
        )?;
        let outputs = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("inject_t", [])?,
                function.input_wires(),
            )?
            .outputs()
            .collect::<Vec<_>>();
        function.finish_with_outputs(outputs)?;
        assert!(module.finish_hugr().is_err());
        Ok(())
    }

    #[test]
    fn test_all_ops_serialization() -> Result<(), Box<dyn Error>> {
        // Validate every operation in a function with its complete signature,
        // then round-trip all functions through an envelope and registry.
        let mut module = ModuleBuilder::new();
        for def in HelixOpDef::iter() {
            let concrete = def.instantiate_no_args();
            let op = concrete.to_extension_op()?;
            let loaded = ConcreteHelixOp::from_extension_op(&op)?;
            assert_eq!(loaded.def, def);
            assert!(loaded.type_args().is_empty());
            let mut function =
                module.define_function(def.opdef_id(), op.signature().as_ref().clone())?;
            let outputs = function
                .add_dataflow_op(op, function.input_wires())?
                .outputs()
                .collect::<Vec<_>>();
            function.finish_with_outputs(outputs)?;
        }
        let h = module.finish_hugr()?;
        h.validate()?;
        let package = Package::new([h]);
        let mut bytes = Vec::new();
        write_envelope(
            &mut bytes,
            &package,
            EnvelopeConfig::new(EnvelopeFormat::ModelWithExtensions),
        )?;
        let mut registry: ExtensionRegistry = std_reg();
        registry.extend([
            types_extension.clone(),
            EXTENSION.clone(),
            crate::std::types::EXTENSION.clone(),
        ]);
        let (_, restored) = read_envelope(std::io::BufReader::new(bytes.as_slice()), &registry)?;
        restored.modules[0].validate()?;
        Ok(())
    }

    #[test]
    fn test_block_lifecycle() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function(
            "main",
            Signature::new(vec![], vec![BorrowArray::ty(2, bool_t()); 2]),
        )?;
        let [mut a] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_zero", [])?, [])?
            .outputs_arr();
        let [mut b] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_plus", [])?, [])?
            .outputs_arr();
        let zero = function.add_load_const(Value::extension(ConstInt::new_u(6, 0)?));
        let one = function.add_load_const(Value::extension(ConstInt::new_u(6, 1)?));
        for name in ["x", "y", "z"] {
            [a] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, [])?, [a, one])?
                .outputs_arr();
        }
        for name in ["swap", "cx", "h_all", "cz", "ss", "qec_cycle"] {
            [a] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, [])?, [a])?
                .outputs_arr();
        }
        [a, b] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("cx_between_blocks", [])?,
                [a, b, one, zero],
            )?
            .outputs_arr();
        [a, b] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("cx_transversal", [])?,
                [a, b],
            )?
            .outputs_arr();
        let [mx] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("measure_xx", [])?, [a])?
            .outputs_arr();
        let [mz] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("measure_zz", [])?, [b])?
            .outputs_arr();
        let [unused] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_zero", [])?, [])?
            .outputs_arr();
        function.add_dataflow_op(EXTENSION.instantiate_extension_op("free", [])?, [unused])?;
        let decode = crate::std::ops::EXTENSION.instantiate_extension_op("decode", [2.into()])?;
        let [mx] = function
            .add_dataflow_op(decode.clone(), [mx])?
            .outputs_arr();
        let [mz] = function.add_dataflow_op(decode, [mz])?.outputs_arr();
        function.finish_with_outputs([mx, mz])?;
        module.finish_hugr()?.validate()?;
        Ok(())
    }

    #[test]
    fn test_invalid_ops() {
        for def in HelixOpDef::iter() {
            assert!(def.instantiate(&[2.into()]).is_err());
            assert!(
                EXTENSION
                    .instantiate_extension_op(&def.opdef_id(), [2.into()])
                    .is_err()
            );
        }
        let steane_x = crate::steane::ops::EXTENSION
            .instantiate_extension_op("x", [])
            .unwrap();
        assert!(ConcreteHelixOp::from_extension_op(&steane_x).is_err());
    }
}
