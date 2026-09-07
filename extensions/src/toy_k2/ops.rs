use crate::toy_k2::types::{
    logical_block_measurement_type, logical_block_type, logical_qubit_measurement_type,
};
use documented::DocumentedVariants;
use hugr::Extension;
use hugr::extension::prelude::bool_t;
use hugr::extension::simple_op::{
    HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError, try_from_name,
};
use hugr::extension::{ExtensionId, OpDef, SignatureFunc};
use hugr::ops::{ExtensionOp, OpName};
use hugr::std_extensions::arithmetic::int_types::int_type;
use hugr::types::{FuncValueType, Signature, TypeArg};
use std::sync::{Arc, LazyLock, Weak};
use strum::{EnumIter, EnumString, IntoStaticStr};

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.toy_k2.ops");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Logical ToyK2 operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum ToyK2OpDef {
    /// Apply an X gate on a chosen logical qubit of a ToyK2 block.
    x,
    /// Apply a Z gate on a chosen logical qubit of a ToyK2 block.
    z,
    /// Apply an H gate on both logical qubits of a ToyK2 block.
    h_both,
    /// Apply a CX gate within a ToyK2 block, specifying which logical qubit is the target.
    cx_within,
    /// Apply two CX gates in parallel (transversal) between two ToyK2 blocks.
    cx_transversal,
    /// Swap the two logical qubits of a ToyK2 block.
    swap_within,
    /// Prepare a ToyK2 block with both logical qubits on the |0> state.
    prep_zero_ft,
    /// Prepare a ToyK2 block with both logical qubits on the |Y>|Y> state.
    prep_y_state_non_ft,
    /// Prepare a ToyK2 block with both logical qubits on the T|+>T|+> state.
    prep_t_state_non_ft,
    /// Destructively measure a ToyK2 block in the Z basis.
    measure_z_both,
    /// Measure a logical qubit of a ToyK2 block non-destructively in the Z basis.
    measure_z_single,
    /// Apply a error detection cycle on a ToyK2 block.
    qed_cycle,
    /// Decode a qubit measurement of a ToyK2 block.
    decode_qubit_measurement,
    /// Decode a block measurement (both qubits) of a ToyK2 block.
    decode_block_measurement,
    /// Free a logical ToyK2 block.
    free,
}

/// Concrete ToyK2 logical operation.
pub struct ConcreteToyK2Op {
    /// The kind of operation.
    pub def: ToyK2OpDef,
}

impl HasConcrete for ToyK2OpDef {
    type Concrete = ConcreteToyK2Op;

    fn instantiate(&self, _args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        Ok(ConcreteToyK2Op { def: *self })
    }
}

impl HasDef for ConcreteToyK2Op {
    type Def = ToyK2OpDef;
}

impl MakeExtensionOp for ConcreteToyK2Op {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        let def = ToyK2OpDef::from_def(ext_op.def())?;
        def.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        vec![]
    }
}

impl MakeRegisteredOp for ConcreteToyK2Op {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl ToyK2OpDef {
    /// Initialise a [`ConcreteToyK2Op`] from a [`ToyK2OpDef`].
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteToyK2Op {
        ConcreteToyK2Op { def: self }
    }
}

/// Signature of an operation consisting only of logical qubits
fn sig_blocks(n_blocks_in: usize, n_blocks_out: usize) -> SignatureFunc {
    Signature::new(
        vec![logical_block_type(); n_blocks_in],
        vec![logical_block_type(); n_blocks_out],
    )
    .into()
}

/// Signature of an operation acting on a single qubit, addressed by an index
fn sig_addressable() -> SignatureFunc {
    Signature::new(
        vec![logical_block_type(), int_type(1)],
        vec![logical_block_type()],
    )
    .into()
}

impl MakeOpDef for ToyK2OpDef {
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
        use ToyK2OpDef::*;
        match self {
            x => sig_addressable(),
            z => sig_addressable(),
            h_both => sig_blocks(1, 1),
            cx_within => sig_addressable(),
            cx_transversal => sig_blocks(2, 2),
            swap_within => sig_blocks(1, 1),
            prep_zero_ft => sig_blocks(0, 1),
            prep_y_state_non_ft => sig_blocks(0, 1),
            prep_t_state_non_ft => sig_blocks(0, 1),
            qed_cycle => sig_blocks(1, 1),
            free => sig_blocks(1, 0),
            measure_z_both => FuncValueType::new(
                vec![logical_block_type()],
                vec![logical_block_measurement_type()],
            )
            .into(),
            measure_z_single => FuncValueType::new(
                vec![logical_block_type(), int_type(1)],
                vec![logical_block_type(), logical_qubit_measurement_type()],
            )
            .into(),
            decode_qubit_measurement => {
                FuncValueType::new(vec![logical_qubit_measurement_type()], vec![bool_t()]).into()
            }
            decode_block_measurement => {
                FuncValueType::new(vec![logical_block_measurement_type()], vec![bool_t(); 2]).into()
            }
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for logical ToyK2 operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        ToyK2OpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::toy_k2::types::EXTENSION as types_extension;
    use hugr::builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder};
    use hugr::envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope};
    use hugr::extension::ExtensionRegistry;
    use hugr::ops::DataflowOpTrait;
    use hugr::package::Package;
    use hugr::std_extensions::arithmetic::int_types::ConstInt;
    use hugr::std_extensions::std_reg;
    use hugr::types::Signature;
    use hugr::{CircuitUnit, HugrView};
    use std::error::Error;

    #[test]
    fn test_toy_k2_ops_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.toy_k2.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 15);
    }

    #[test]
    fn test_signatures() {
        assert_eq!(
            ToyK2OpDef::prep_zero_ft
                .instantiate_no_args()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([], [logical_block_type()])
        );
        assert_eq!(
            ToyK2OpDef::prep_t_state_non_ft
                .instantiate_no_args()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([], [logical_block_type()])
        );
        assert_eq!(
            ToyK2OpDef::prep_y_state_non_ft
                .instantiate_no_args()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([], [logical_block_type()])
        );
    }

    #[test]
    fn test_linear_ops() -> Result<(), Box<dyn Error>> {
        let x = EXTENSION.instantiate_extension_op("x", [])?;
        let z = EXTENSION.instantiate_extension_op("z", [])?;
        let h_both = EXTENSION.instantiate_extension_op("h_both", [])?;
        let cx_within = EXTENSION.instantiate_extension_op("cx_within", [])?;
        let cx_transversal = EXTENSION.instantiate_extension_op("cx_transversal", [])?;
        let swap_within = EXTENSION.instantiate_extension_op("swap_within", [])?;
        let qed_cycle = EXTENSION.instantiate_extension_op("qed_cycle", [])?;

        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![logical_block_type(); 2]);
        let mut f_build = module_builder.define_function("main", signature)?;
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        let index0 = linear.add_constant(ConstInt::new_u(1, 0).unwrap());
        let index1 = linear.add_constant(ConstInt::new_u(1, 1).unwrap());
        let index2 = linear.add_constant(ConstInt::new_u(1, 0).unwrap());
        linear
            .append_and_consume(x, [CircuitUnit::Linear(0), CircuitUnit::Wire(index0)])?
            .append_and_consume(z, [CircuitUnit::Linear(1), CircuitUnit::Wire(index1)])?
            .append(h_both, [0])?
            .append_and_consume(
                cx_within,
                [CircuitUnit::Linear(1), CircuitUnit::Wire(index2)],
            )?
            .append(cx_transversal, [0, 1])?
            .append(swap_within, [0])?
            .append(qed_cycle, [1])?;
        let outs = linear.finish();
        f_build.finish_with_outputs(outs)?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_prep_measure_decode_qubit_free() -> Result<(), Box<dyn Error>> {
        let prep_zero_ft = EXTENSION.instantiate_extension_op("prep_zero_ft", [])?;
        let free = EXTENSION.instantiate_extension_op("free", [])?;
        let measure_z_single = EXTENSION.instantiate_extension_op("measure_z_single", [])?;
        let decode_qubit_measurement =
            EXTENSION.instantiate_extension_op("decode_qubit_measurement", [])?;

        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(vec![], vec![bool_t()]);
        let mut f_build = module_builder.define_function("main", signature)?;

        let [blk] = f_build
            .add_dataflow_op(prep_zero_ft.clone(), vec![])?
            .outputs_arr();
        let constant = f_build.add_load_value(ConstInt::new_u(1, 0).unwrap());
        let [blk, meas] = f_build
            .add_dataflow_op(measure_z_single, [blk, constant])?
            .outputs_arr();
        let [bool_wire] = f_build
            .add_dataflow_op(decode_qubit_measurement, [meas])?
            .outputs_arr();
        f_build.add_dataflow_op(free, [blk])?;

        f_build.finish_with_outputs([bool_wire])?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_prep_measure_decode_block() -> Result<(), Box<dyn Error>> {
        let prep_zero_ft = EXTENSION.instantiate_extension_op("prep_zero_ft", [])?;
        let measure_z_both = EXTENSION.instantiate_extension_op("measure_z_both", [])?;
        let decode_block_measurement =
            EXTENSION.instantiate_extension_op("decode_block_measurement", [])?;

        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(vec![], vec![bool_t(); 2]);
        let mut f_build = module_builder.define_function("main", signature)?;

        let handle = f_build.add_dataflow_op(prep_zero_ft.clone(), vec![])?;
        let handle = f_build.add_dataflow_op(measure_z_both, handle.outputs())?;
        let [bool_wire0, bool_wire1] = f_build
            .add_dataflow_op(decode_block_measurement, handle.outputs())?
            .outputs_arr();

        f_build.finish_with_outputs([bool_wire0, bool_wire1])?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_serialization() {
        let block_type = logical_block_type();
        let measurent_block_type = logical_block_measurement_type();
        let measure_z_both = EXTENSION
            .instantiate_extension_op("measure_z_both", [])
            .unwrap();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(vec![block_type], vec![measurent_block_type]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(measure_z_both, [0]).unwrap();
        let outs = linear.finish();
        f_build.finish_with_outputs(outs).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        let package = Package::new([h]);
        let mut bytes: Vec<u8> = Vec::new();
        write_envelope(
            &mut bytes,
            &package,
            EnvelopeConfig::new(EnvelopeFormat::ModelWithExtensions),
        )
        .unwrap();
        let buff = std::io::BufReader::new(bytes.as_slice());
        let mut reg: ExtensionRegistry = std_reg();
        reg.extend([types_extension.clone(), EXTENSION.clone()]);
        let (_, package1) = read_envelope(buff, &reg).unwrap();
        let h1 = &package1.modules[0];
        h1.validate().unwrap();
    }
}
