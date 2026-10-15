//! Extension providing logical operations on C4-Helix codeblocks.
//!
//! Gates have ideal logical semantics, including any required Pauli-frame
//! corrections in their implementations. Addressable operations take runtime
//! logical indices (0 or 1); invalid indices cause a runtime panic.
//!
//! T-state preparation requests a resource from a backend-selected factory.
//! Injection consumes the resource and includes measurement, feed-forward, and
//! Clifford corrections in its ideal gate contract.
use std::sync::{Arc, LazyLock, Weak};

use documented::DocumentedVariants;
use hugr::{
    Extension,
    extension::{
        ExtensionId, OpDef, SignatureError, SignatureFromArgs, SignatureFunc,
        simple_op::{
            HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError,
            try_from_name,
        },
    },
    ops::{ExtensionOp, OpName},
    std_extensions::arithmetic::int_types::int_type,
    types::{FuncValueType, PolyFuncTypeRV, Signature, TypeArg, type_param::TypeParam},
};

use super::types::{block_type, borrowed_block_type, dynamic_logical_qubit_type, t_state_type};
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
    /// Discard a block in any logical state.
    free,
    /// Apply X to the logical qubit selected by a runtime index.
    x,
    /// Apply Y to the logical qubit selected by a runtime index.
    y,
    /// Apply Z to the logical qubit selected by a runtime index.
    z,
    /// Swap the two qubits in the block.
    swap,
    /// CX from logical qubit 0 to 1, then SWAP: |a,b> -> |a XOR b,a>.
    cx_swap,
    /// Hadamard on each logical qubit followed by SWAP.
    hh_swap,
    /// Logical CZ: |a,b> -> (-1)^(ab)|a,b>.
    /// Lowering must compensate the physical gadget's residual Z on qubit 1.
    cz,
    /// Logical S on both qubits: |a,b> -> i^(a+b)|a,b>.
    /// Lowering must compensate the physical gadget's residual Z on both qubits
    /// and include the flagging and syndrome extraction required for fault tolerance.
    ss,
    /// Targeted CX from the first block to the second.
    /// Runtime indices select the control and target; the other qubits are unchanged.
    cx_between_blocks,
    /// Apply CX from each logical qubit in the first block to the corresponding
    /// logical qubit in the second block, preserving block order.
    cx_transversal,
    /// Destructively measure both logical qubits in the X basis.
    /// Return a two-outcome logical measurement, ordered by logical index.
    /// Decoded bit b denotes eigenvalue (-1)^b; this is not an XX parity measurement.
    measure_xx,
    /// Destructively measure both logical qubits in the Z basis.
    /// Return a two-outcome logical measurement, ordered by logical index.
    /// Decoded bit b denotes eigenvalue (-1)^b; this is not a ZZ parity measurement.
    measure_zz,
    /// Perform syndrome extraction and recovery (or a Pauli-frame update).
    /// Ideally preserves the logical state, including external entanglement.
    qec_cycle,
    /// Allocate a dynamic logical qubit in the |0> state.
    /// Its physical block and logical position are assigned at runtime.
    alloc_dynq,
    /// Discard a dynamic logical qubit in any state without changing its partner.
    free_dynq,
    /// Apply logical X to a dynamic qubit, leaving its block partner unchanged.
    x_dynq,
    /// Apply logical Y to a dynamic qubit, leaving its block partner unchanged.
    y_dynq,
    /// Apply logical Z to a dynamic qubit, leaving its block partner unchanged.
    z_dynq,
    /// Apply logical Hadamard to a dynamic qubit, leaving its block partner unchanged.
    h_dynq,
    /// Apply logical S = diag(1, i) to a dynamic qubit, leaving its partner unchanged.
    s_dynq,
    /// Apply logical S dagger = diag(1, -i) to a dynamic qubit.
    sdg_dynq,
    /// Apply logical CX with the first dynamic qubit controlling the second.
    /// The inputs may belong to the same block or different blocks.
    cx_dynq,
    /// Apply logical CZ to two dynamic qubits, regardless of block membership.
    cz_dynq,
    /// Exchange the logical states of two dynamic qubits, preserving output order.
    swap_dynq,
    /// Destructively measure a dynamic qubit in the X basis, preserving its partner.
    /// The decoded bit b denotes eigenvalue (-1)^b.
    measure_x_dynq,
    /// Destructively measure a dynamic qubit in the Z basis, preserving its partner.
    /// The decoded bit b denotes eigenvalue (-1)^b.
    measure_z_dynq,
    /// Borrow m logical qubits selected by distinct runtime indices (0 or 1).
    /// Takes a block followed by m indices; returns a borrowed block followed
    /// by m dynamic qubits in index-input order. Static parameter m is in 0..=2.
    /// Preserves the joint state and each qubit's originating block and index.
    borrow,
    /// Borrow m additional logical qubits from a borrowed block.
    /// Takes a borrowed block followed by m distinct, currently unborrowed indices;
    /// returns the borrowed block followed by m dynamic qubits in index-input order.
    /// Invalid indices or outstanding borrows of those indices cause a runtime panic.
    borrow_more,
    /// Return m borrowed qubits to their originating block and logical positions.
    /// Takes the borrowed block followed by m qubits; returns the borrowed block.
    /// Qubit order is immaterial; wrong-block or invalid handles cause a runtime panic.
    restore_some,
    /// Return the final m borrowed qubits and recover the owning block.
    /// Takes the borrowed block followed by m qubits; returns a block.
    /// Panics at runtime for invalid provenance or remaining outstanding borrows.
    /// All borrow/restore operations have a single static count m in 0..=2.
    restore,
    /// Supply a resource with ideal state (|0> + exp(i*pi/4)|1>)/sqrt(2).
    /// The backend chooses the factory and encoding, and handles heralded retries.
    /// Preparation need not occur inside a Helix block.
    prep_t_state,
    /// Consume a T-state resource and apply T = diag(1, exp(i*pi/4)) to the
    /// logical qubit selected by a runtime index, preserving its block partner.
    /// Inputs are (block, index, resource); measurement and feed-forward
    /// corrections are included, leaving no outstanding Clifford correction.
    inject_t,
    /// Consume the same T-state resource as inject_t and apply T dagger to
    /// the indexed logical qubit, preserving its block partner. Inputs are
    /// (block, index, resource); all measurement and Clifford corrections are included.
    inject_tdg,
    /// Consume a T-state resource and apply T to a dynamic logical qubit.
    /// Inputs are (qubit, resource). Preserves its partner and includes all
    /// measurement, feed-forward, and Clifford corrections.
    inject_t_dynq,
    /// Consume a T-state resource and apply T dagger to a dynamic logical qubit.
    /// Inputs are (qubit, resource). Preserves its partner and includes all
    /// measurement, feed-forward, and Clifford corrections.
    inject_tdg_dynq,
    /// Discard an unused T-state resource.
    free_t_state,
}

/// Concrete Helix logical operation.
pub struct ConcreteHelixOp {
    /// The kind of operation.
    pub def: HelixOpDef,

    /// Complete static arguments (a count for borrow/restore operations, otherwise empty).
    pub args: Vec<TypeArg>,
}

impl HasConcrete for HelixOpDef {
    type Concrete = ConcreteHelixOp;

    fn instantiate(&self, args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        if matches!(
            self,
            Self::borrow | Self::borrow_more | Self::restore_some | Self::restore
        ) {
            self.compute_signature(args)?;
        } else if !args.is_empty() {
            return Err(SignatureError::InvalidTypeArgs.into());
        }
        Ok(ConcreteHelixOp {
            def: *self,
            args: args.to_vec(),
        })
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
        self.args.clone()
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
    /// Borrow/restore operations must instead be instantiated with a count.
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteHelixOp {
        ConcreteHelixOp {
            def: self,
            args: vec![],
        }
    }
}

/// Signature with block inputs followed by runtime logical indices.
fn sig_blocks(n_in: usize, n_out: usize, n_indices: usize) -> SignatureFunc {
    let mut inputs = vec![block_type(); n_in];
    inputs.extend(vec![int_type(6); n_indices]);
    Signature::new(inputs, vec![block_type(); n_out]).into()
}

/// Signature of an operation on independently owned dynamic logical qubits.
fn sig_dynq(n_in: usize, n_out: usize) -> SignatureFunc {
    Signature::new(
        vec![dynamic_logical_qubit_type(); n_in],
        vec![dynamic_logical_qubit_type(); n_out],
    )
    .into()
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
            inject_t_dynq | inject_tdg_dynq => Signature::new(
                [dynamic_logical_qubit_type(), t_state_type()],
                [dynamic_logical_qubit_type()],
            )
            .into(),
            alloc_dynq => sig_dynq(0, 1),
            free_dynq => sig_dynq(1, 0),
            x_dynq | y_dynq | z_dynq | h_dynq | s_dynq | sdg_dynq => sig_dynq(1, 1),
            cx_dynq | cz_dynq | swap_dynq => sig_dynq(2, 2),
            measure_x_dynq | measure_z_dynq => Signature::new(
                [dynamic_logical_qubit_type()],
                [logical_measurement_type(1)],
            )
            .into(),
            borrow | borrow_more | restore_some | restore => (*self).into(),
            alloc_zero | alloc_plus => sig_blocks(0, 1, 0),
            free => sig_blocks(1, 0, 0),
            x | y | z => sig_blocks(1, 1, 1),
            swap | cx_swap | hh_swap | cz | ss | qec_cycle => sig_blocks(1, 1, 0),
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

/// Static count of logical qubits borrowed or restored.
const STATIC_NAT_PARAM: &[TypeParam; 1] = &[TypeParam::max_nat_kind()];

impl SignatureFromArgs for HelixOpDef {
    fn compute_signature(&self, arg_values: &[TypeArg]) -> Result<PolyFuncTypeRV, SignatureError> {
        let [TypeArg::BoundedNat(m @ 0..=2)] = *arg_values else {
            return Err(SignatureError::InvalidTypeArgs);
        };
        let m = m as usize;
        let (inputs, outputs) = match self {
            Self::borrow | Self::borrow_more => {
                let owner = if matches!(self, Self::borrow) {
                    block_type()
                } else {
                    borrowed_block_type()
                };
                let mut inputs = vec![owner];
                inputs.extend(vec![int_type(6); m]);
                let mut outputs = vec![borrowed_block_type()];
                outputs.extend(vec![dynamic_logical_qubit_type(); m]);
                (inputs, outputs)
            }
            Self::restore_some | Self::restore => {
                let mut inputs = vec![borrowed_block_type()];
                inputs.extend(vec![dynamic_logical_qubit_type(); m]);
                let owner = if matches!(self, Self::restore) {
                    block_type()
                } else {
                    borrowed_block_type()
                };
                (inputs, vec![owner])
            }
            _ => return Err(SignatureError::InvalidTypeArgs),
        };
        Ok(PolyFuncTypeRV::new(
            vec![],
            FuncValueType::new(inputs, outputs),
        ))
    }

    fn static_params(&self) -> &[TypeParam] {
        STATIC_NAT_PARAM
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
        assert_eq!(EXTENSION.operations().count(), 39);
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
    fn test_dynamic_signatures() -> Result<(), Box<dyn Error>> {
        let qubit = dynamic_logical_qubit_type();
        for (name, expected) in [
            ("alloc_dynq", Signature::new(vec![], [qubit.clone()])),
            ("free_dynq", Signature::new([qubit.clone()], vec![])),
        ] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &expected
            );
        }
        for name in ["x_dynq", "y_dynq", "z_dynq", "h_dynq", "s_dynq", "sdg_dynq"] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &Signature::new_endo([qubit.clone()])
            );
        }
        for name in ["cx_dynq", "cz_dynq", "swap_dynq"] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &Signature::new_endo([qubit.clone(), qubit.clone()])
            );
        }
        for name in ["measure_x_dynq", "measure_z_dynq"] {
            assert_eq!(
                EXTENSION
                    .instantiate_extension_op(name, [])?
                    .signature()
                    .as_ref(),
                &Signature::new([qubit.clone()], [logical_measurement_type(1)])
            );
        }
        Ok(())
    }

    #[test]
    fn test_dynamic_lifecycle() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function(
            "main",
            Signature::new(
                vec![],
                [BorrowArray::ty(1, bool_t()), BorrowArray::ty(1, bool_t())],
            ),
        )?;
        let [mut a] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_dynq", [])?, [])?
            .outputs_arr();
        let [mut b] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_dynq", [])?, [])?
            .outputs_arr();
        for name in ["x_dynq", "y_dynq", "z_dynq", "h_dynq", "s_dynq", "sdg_dynq"] {
            [a] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, [])?, [a])?
                .outputs_arr();
        }
        // Exercise gates on independently allocated dynamic qubits.
        [a, b] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("cx_dynq", [])?, [a, b])?
            .outputs_arr();
        let [mut c] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_dynq", [])?, [])?
            .outputs_arr();
        for name in ["cx_dynq", "cz_dynq", "swap_dynq"] {
            [a, c] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op(name, [])?, [a, c])?
                .outputs_arr();
        }
        let [mx] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("measure_x_dynq", [])?,
                [a],
            )?
            .outputs_arr();
        let [mz] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("measure_z_dynq", [])?,
                [c],
            )?
            .outputs_arr();
        let decode = crate::std::ops::EXTENSION.instantiate_extension_op("decode", [1.into()])?;
        let [mx] = function
            .add_dataflow_op(decode.clone(), [mx])?
            .outputs_arr();
        let [mz] = function.add_dataflow_op(decode, [mz])?.outputs_arr();
        function.add_dataflow_op(EXTENSION.instantiate_extension_op("free_dynq", [])?, [b])?;
        let [unused] = function
            .add_dataflow_op(EXTENSION.instantiate_extension_op("alloc_dynq", [])?, [])?
            .outputs_arr();
        function.add_dataflow_op(
            EXTENSION.instantiate_extension_op("free_dynq", [])?,
            [unused],
        )?;
        function.finish_with_outputs([mx, mz])?;
        module.finish_hugr()?.validate()?;
        Ok(())
    }

    #[test]
    fn test_borrow_restore() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function("main", Signature::new_endo([block_type()]))?;
        let [block] = function.input_wires_arr();
        let zero = function.add_load_const(Value::extension(ConstInt::new_u(6, 0)?));
        let one = function.add_load_const(Value::extension(ConstInt::new_u(6, 1)?));
        let [owner, first] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("borrow", [1.into()])?,
                [block, zero],
            )?
            .outputs_arr();
        let [owner, second] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("borrow_more", [1.into()])?,
                [owner, one],
            )?
            .outputs_arr();
        let [first, second] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("cx_dynq", [])?,
                [first, second],
            )?
            .outputs_arr();
        let [owner] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("restore_some", [1.into()])?,
                [owner, second],
            )?
            .outputs_arr();
        let [block] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("restore", [1.into()])?,
                [owner, first],
            )?
            .outputs_arr();
        // Borrow both in reversed index order, then restore in another order.
        let [owner, second, first] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("borrow", [2.into()])?,
                [block, one, zero],
            )?
            .outputs_arr();
        let [owner] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("restore_some", [2.into()])?,
                [owner, first, second],
            )?
            .outputs_arr();
        let [block] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("restore", [0.into()])?,
                [owner],
            )?
            .outputs_arr();
        function.finish_with_outputs([block])?;
        module.finish_hugr()?.validate()?;
        Ok(())
    }

    #[test]
    fn test_borrow_restore_signatures() -> Result<(), Box<dyn Error>> {
        for m in 0..=2 {
            for name in ["borrow", "borrow_more", "restore_some", "restore"] {
                let borrowing = matches!(name, "borrow" | "borrow_more");
                let mut inputs = vec![if name == "borrow" {
                    block_type()
                } else {
                    borrowed_block_type()
                }];
                inputs.extend(vec![
                    if borrowing {
                        int_type(6)
                    } else {
                        dynamic_logical_qubit_type()
                    };
                    m
                ]);
                let mut outputs = vec![if name == "restore" {
                    block_type()
                } else {
                    borrowed_block_type()
                }];
                if borrowing {
                    outputs.extend(vec![dynamic_logical_qubit_type(); m]);
                }
                let args = [TypeArg::from(m as u64)];
                let op = EXTENSION.instantiate_extension_op(name, args.clone())?;
                assert_eq!(op.signature().as_ref(), &Signature::new(inputs, outputs));
                let concrete = ConcreteHelixOp::from_extension_op(&op)?;
                assert_eq!(concrete.type_args(), args);
            }
        }
        Ok(())
    }

    #[test]
    fn test_restore_rejects_duplicate_qubit() {
        let mut module = ModuleBuilder::new();
        let mut function = module
            .define_function(
                "bad_restore",
                Signature::new(
                    [borrowed_block_type(), dynamic_logical_qubit_type()],
                    [block_type()],
                ),
            )
            .unwrap();
        let [owner, qubit] = function.input_wires_arr();
        assert!(
            function
                .add_dataflow_op(
                    EXTENSION
                        .instantiate_extension_op("restore", [2.into()])
                        .unwrap(),
                    [owner, qubit, qubit],
                )
                .is_err()
        );
    }

    #[test]
    fn test_borrowed_block_rejects_block_gate() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function(
            "bad",
            Signature::new([borrowed_block_type()], [block_type()]),
        )?;
        let outputs = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("qec_cycle", [])?,
                function.input_wires(),
            )?
            .outputs()
            .collect::<Vec<_>>();
        function.finish_with_outputs(outputs)?;
        assert!(module.finish_hugr().is_err());
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
        let [owner, mut first, mut second] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("borrow", [2.into()])?,
                [block, zero, one],
            )?
            .outputs_arr();
        for (name, target) in [
            ("inject_t_dynq", &mut first),
            ("inject_tdg_dynq", &mut second),
        ] {
            let [resource] = function
                .add_dataflow_op(EXTENSION.instantiate_extension_op("prep_t_state", [])?, [])?
                .outputs_arr();
            [*target] = function
                .add_dataflow_op(
                    EXTENSION.instantiate_extension_op(name, [])?,
                    [*target, resource],
                )?
                .outputs_arr();
        }
        [block] = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("restore", [2.into()])?,
                [owner, first, second],
            )?
            .outputs_arr();
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
            (
                "inject_t_dynq",
                Signature::new(
                    [dynamic_logical_qubit_type(), t_state_type()],
                    [dynamic_logical_qubit_type()],
                ),
            ),
            (
                "inject_tdg_dynq",
                Signature::new(
                    [dynamic_logical_qubit_type(), t_state_type()],
                    [dynamic_logical_qubit_type()],
                ),
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
    fn test_injection_rejects_ordinary_qubit_resource() -> Result<(), Box<dyn Error>> {
        let mut module = ModuleBuilder::new();
        let mut function = module.define_function(
            "bad",
            Signature::new(
                vec![dynamic_logical_qubit_type(); 2],
                [dynamic_logical_qubit_type()],
            ),
        )?;
        let outputs = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("inject_t_dynq", [])?,
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
            let args = if matches!(
                def,
                HelixOpDef::borrow
                    | HelixOpDef::borrow_more
                    | HelixOpDef::restore_some
                    | HelixOpDef::restore
            ) {
                vec![2.into()]
            } else {
                vec![]
            };
            let concrete = def.instantiate(&args)?;
            let op = concrete.to_extension_op()?;
            let loaded = ConcreteHelixOp::from_extension_op(&op)?;
            assert_eq!(loaded.def, def);
            assert_eq!(loaded.type_args(), args);
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
        for name in ["swap", "cx_swap", "hh_swap", "cz", "ss", "qec_cycle"] {
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
            let invalid_args = if matches!(
                def,
                HelixOpDef::borrow
                    | HelixOpDef::borrow_more
                    | HelixOpDef::restore_some
                    | HelixOpDef::restore
            ) {
                vec![
                    vec![],
                    vec![3.into()],
                    vec![u64::MAX.into()],
                    vec![1.into(), 2.into()],
                    vec!["one".into()],
                ]
            } else {
                vec![vec![2.into()]]
            };
            for args in invalid_args {
                assert!(def.instantiate(&args).is_err());
                assert!(
                    EXTENSION
                        .instantiate_extension_op(&def.opdef_id(), args)
                        .is_err()
                );
            }
        }
        let steane_x = crate::steane::ops::EXTENSION
            .instantiate_extension_op("x", [])
            .unwrap();
        assert!(ConcreteHelixOp::from_extension_op(&steane_x).is_err());

        // A dynamic logical qubit cannot stand in for an entire two-qubit block.
        let mut module = ModuleBuilder::new();
        let mut function = module
            .define_function(
                "bad",
                Signature::new([dynamic_logical_qubit_type()], [block_type()]),
            )
            .unwrap();
        let outputs = function
            .add_dataflow_op(
                EXTENSION.instantiate_extension_op("swap", []).unwrap(),
                function.input_wires(),
            )
            .unwrap()
            .outputs()
            .collect::<Vec<_>>();
        function.finish_with_outputs(outputs).unwrap();
        assert!(module.finish_hugr().is_err());
    }
}
