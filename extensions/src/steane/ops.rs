//! Extension providing logical operations on Steane codeblocks.

use std::sync::{Arc, LazyLock, Weak};

use crate::steane::types::{logical_measurement_type, logical_qubit_type};
use documented::DocumentedVariants;
use hugr::extension::prelude::bool_t;
use hugr::{
    Extension,
    extension::{
        ExtensionId, OpDef, SignatureFunc,
        simple_op::{
            HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError,
            try_from_name,
        },
    },
    ops::{ExtensionOp, OpName},
    types::{FuncValueType, Signature, TypeArg},
};
use strum::{EnumIter, EnumString, IntoStaticStr};
use tket::extension::rotation::rotation_type;

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.steane.ops");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 2);

/// Logical Steane operations.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum SteaneOpDef {
    /// Prepare a logical zero state.
    prep_zero,
    /// Free a qubit.
    free,
    /// Destructive measurement of a logical qubit in the Z basis.
    measure_z,
    /// Decode
    decode,
    /// Perform a QEC cycle on logical qubit
    qec_cycle,
    /// X gate.
    x,
    /// Z gate.
    y,
    /// Y gate.
    z,
    /// H gate.
    h,
    /// S gate.
    s,
    /// S dagger gate.
    sdg,
    /// Rz gate
    rz,
    /// Prepare a magic state that can be used to produce T-like states (T and Tdg).
    prep_magic_for_t_like,
    /// Perform a T gate by injecting a magic state.
    inject_magic_for_t,
    /// Perform a Tdg gate by injecting a magic state.
    inject_magic_for_tdg,
    /// CX gate.
    cx,
    /// Swap of two qubits.
    swap,
}

/// Concrete Steane logical operation.
pub struct ConcreteSteaneOp {
    /// The kind of operation.
    pub def: SteaneOpDef,
}

impl HasConcrete for SteaneOpDef {
    type Concrete = ConcreteSteaneOp;

    fn instantiate(&self, _args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        Ok(ConcreteSteaneOp { def: *self })
    }
}

impl HasDef for ConcreteSteaneOp {
    type Def = SteaneOpDef;
}

impl MakeExtensionOp for ConcreteSteaneOp {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        let def = SteaneOpDef::from_def(ext_op.def())?;
        def.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        vec![]
    }
}

impl MakeRegisteredOp for ConcreteSteaneOp {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl SteaneOpDef {
    /// Initialise a [`ConcreteSteaneOp`] from a [`SteaneOpDef`].
    #[must_use]
    pub fn instantiate_no_args(self) -> ConcreteSteaneOp {
        ConcreteSteaneOp { def: self }
    }
}

/// Signature of an operation consisting only of logical qubits
fn sig_qubits(n_qubits_in: usize, n_qubits_out: usize) -> SignatureFunc {
    Signature::new(
        vec![logical_qubit_type(); n_qubits_in],
        vec![logical_qubit_type(); n_qubits_out],
    )
    .into()
}

impl MakeOpDef for SteaneOpDef {
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
        use SteaneOpDef::*;
        match self {
            prep_zero => sig_qubits(0, 1),
            free => sig_qubits(1, 0),
            measure_z => {
                FuncValueType::new(vec![logical_qubit_type()], vec![logical_measurement_type()])
                    .into()
            }
            decode => FuncValueType::new(vec![logical_measurement_type()], vec![bool_t()]).into(),
            qec_cycle => {
                FuncValueType::new(vec![logical_qubit_type()], vec![logical_qubit_type()]).into()
            }
            x => sig_qubits(1, 1),
            y => sig_qubits(1, 1),
            z => sig_qubits(1, 1),
            h => sig_qubits(1, 1),
            s => sig_qubits(1, 1),
            sdg => sig_qubits(1, 1),
            rz => FuncValueType::new(
                vec![logical_qubit_type(), rotation_type()],
                [logical_qubit_type()],
            )
            .into(),
            prep_magic_for_t_like => sig_qubits(0, 1),
            inject_magic_for_t => sig_qubits(2, 1),
            inject_magic_for_tdg => sig_qubits(2, 1),
            cx => sig_qubits(2, 2),
            swap => sig_qubits(2, 2),
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for logical Steane operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        SteaneOpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use super::*;
    use crate::steane::types::EXTENSION as types_extension;
    use hugr::{
        HugrView,
        builder::{Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
        envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope},
        extension::ExtensionRegistry,
        ops::DataflowOpTrait,
        package::Package,
        std_extensions::std_reg,
        types::Signature,
    };
    use std::error::Error;

    #[test]
    fn test_steane_ops_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.steane.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 17);
    }

    #[test]
    fn test_signatures() {
        assert_eq!(
            SteaneOpDef::x
                .instantiate_no_args()
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([logical_qubit_type()], [logical_qubit_type()])
        );
    }

    #[test]
    fn test_linear_ops() -> Result<(), Box<dyn Error>> {
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![logical_qubit_type(); 2]);
        let mut f_build = module_builder.define_function("main", signature)?;
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear
            .append(EXTENSION.instantiate_extension_op("x", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("y", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("z", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("h", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("s", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("sdg", [])?, [0])?
            .append(EXTENSION.instantiate_extension_op("cx", [])?, [0, 1])?
            .append(EXTENSION.instantiate_extension_op("swap", [])?, [0, 1])?;
        let outs = linear.finish();
        f_build.finish_with_outputs(outs)?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_prep_free_measure_decode() -> Result<(), Box<dyn Error>> {
        let prep_zero = EXTENSION.instantiate_extension_op("prep_zero", [])?;
        let free = EXTENSION.instantiate_extension_op("free", [])?;
        let measure_z = EXTENSION.instantiate_extension_op("measure_z", [])?;
        let decode = EXTENSION.instantiate_extension_op("decode", [])?;
        let prep_magic_for_t_like =
            EXTENSION.instantiate_extension_op("prep_magic_for_t_like", [])?;
        let inject_magic_for_t = EXTENSION.instantiate_extension_op("inject_magic_for_t", [])?;
        let inject_magic_for_tdg =
            EXTENSION.instantiate_extension_op("inject_magic_for_tdg", [])?;

        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new(
            vec![logical_qubit_type()],
            vec![bool_t(), logical_qubit_type(), logical_qubit_type()],
        );
        let mut f_build = module_builder.define_function("main", signature)?;

        let handle = f_build.add_dataflow_op(free, f_build.input_wires())?;
        assert_eq!(handle.outputs().count(), 0);

        let handle = f_build.add_dataflow_op(prep_zero.clone(), vec![])?;
        let handle = f_build.add_dataflow_op(measure_z, handle.outputs())?;
        let [bool_wire] = f_build
            .add_dataflow_op(decode, handle.outputs())?
            .outputs_arr();

        let [magic] = f_build
            .add_dataflow_op(prep_magic_for_t_like.clone(), vec![])?
            .outputs_arr();
        let [qubit_1] = f_build
            .add_dataflow_op(prep_zero.clone(), vec![])?
            .outputs_arr();
        let [qubit_1] = f_build
            .add_dataflow_op(inject_magic_for_t, vec![qubit_1, magic])?
            .outputs_arr();

        let [magic] = f_build
            .add_dataflow_op(prep_magic_for_t_like, vec![])?
            .outputs_arr();
        let [qubit_2] = f_build.add_dataflow_op(prep_zero, vec![])?.outputs_arr();
        let [qubit_2] = f_build
            .add_dataflow_op(inject_magic_for_tdg, vec![qubit_2, magic])?
            .outputs_arr();

        f_build.finish_with_outputs([bool_wire, qubit_1, qubit_2])?;
        let h = module_builder.finish_hugr()?;
        h.validate()?;
        Ok(())
    }

    #[test]
    fn test_serialization() {
        let qubit = logical_qubit_type();
        let x = EXTENSION.instantiate_extension_op("x", []).unwrap();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![qubit]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(x, [0]).unwrap();
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
