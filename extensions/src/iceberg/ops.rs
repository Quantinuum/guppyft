//! Extension providing logical operations on Iceberg codeblocks.

use std::sync::{Arc, LazyLock, Weak};

use documented::DocumentedVariants;
use hugr::{
    Extension,
    extension::{
        ExtensionId, OpDef, SignatureFunc,
        prelude::{bool_t, option_type},
        simple_op::{
            HasConcrete, HasDef, MakeExtensionOp, MakeOpDef, MakeRegisteredOp, OpLoadError,
            try_from_name,
        },
    },
    ops::{ExtensionOp, OpName},
    std_extensions::{
        arithmetic::{float_types::float64_type, int_types::int_type},
        collections::{array::ArrayKind, borrow_array::BorrowArray},
    },
    types::{FuncValueType, PolyFuncTypeRV, Type, TypeArg, type_param::TypeParam},
};
use strum::{EnumIter, EnumString, IntoStaticStr};
use tket_qsystem::extension::futures::future_type;

use super::types::block_tv;

/// The extension identifier.
pub const EXTENSION_ID: ExtensionId = ExtensionId::new_unchecked("guppyft.iceberg.ops");
/// Extension version.
pub const VERSION: semver::Version = semver::Version::new(0, 1, 0);

/// Logical Iceberg operations.
///
/// Those operations that are "addressable", i.e. are associated with one or
/// more specific logical qubits within the block, have two versions: a "static"
/// version, where the indices are parameters to the operation definition, and a
/// "dynamic" version, where the indices are integer inputs to the operation.
/// The static form provides static guarantees that the indices are within the
/// allowed range, and is simpler to reason about; the dynamic form provides
/// greater flexibility to the programmer.
///
/// The dynamic versions are named with the suffix `_d`: for example `x` is the
/// static form of the X gate and `x_d` is the dynamic form.
#[derive(
    Clone, Copy, Debug, DocumentedVariants, Hash, PartialEq, Eq, EnumIter, IntoStaticStr, EnumString,
)]
#[expect(non_camel_case_types)]
#[non_exhaustive]
pub enum IcebergOpDef {
    /// X gate.
    x,
    /// X gate with dynamic index.
    x_d,
    /// Z gate.
    z,
    /// Z gate with dynamic index.
    z_d,
    /// X gate on two qubits.
    xx,
    /// X gate on two qubits with dynamic indices.
    xx_d,
    /// Y gate on two qubits.
    yy,
    /// Y gate on two qubits with dynamic indices.
    yy_d,
    /// Z gate on two qubits.
    zz,
    /// Z gate on two qubits with dynamic indices.
    zz_d,
    /// X gate on all but one qubit.
    all_but_one_x,
    /// X gate on all but one qubit with dynamic index.
    all_but_one_x_d,
    /// Z gate on all but one qubit.
    all_but_one_z,
    /// Z gate on all but one qubit with dynamic index.
    all_but_one_z_d,
    /// X gate on all qubits.
    all_x,
    /// Y gate on all qubits.
    all_y,
    /// Z gate on all qubits.
    all_z,
    /// X gate on one qubit with Z on all others.
    x_with_all_but_one_z,
    /// X gate on one qubit with Z on all others with dynamic index.
    x_with_all_but_one_z_d,
    /// Z gate on one qubit with X on all others.
    z_with_all_but_one_x,
    /// Z gate on one qubit with X on all others with dynamic index.
    z_with_all_but_one_x_d,
    /// Fan-out from one qubit to all others.
    fan_out,
    /// Fan-out from one qubit to all others with dynamic index.
    fan_out_d,
    /// Fan-in to one qubit from all others.
    fan_in,
    /// Fan-in to one qubit from all others with dynamic index.
    fan_in_d,
    /// Rx gate.
    rx,
    /// Rx gate with dynamic index.
    rx_d,
    /// Rz gate.
    rz,
    /// Rz gate with dynamic index.
    rz_d,
    /// Rx gate on all qubits.
    all_rx,
    /// Ry gate on all qubits.
    all_ry,
    /// Rz gate on all qubits.
    all_rz,
    /// Rx gate on all but one qubit.
    all_but_one_rx,
    /// Rx gate on all but one qubit with dynamic index.
    all_but_one_rx_d,
    /// Rz gate on all but one qubit.
    all_but_one_rz,
    /// Rz gate on all but one qubit with dynamic index.
    all_but_one_rz_d,
    /// H gate on all qubits.
    all_h,
    /// XXPhase gate.
    xx_phase,
    /// XXPhase gate with dynamic indices.
    xx_phase_d,
    /// YYPhase gate.
    yy_phase,
    /// YYPhase gate with dynamic indices.
    yy_phase_d,
    /// ZZPhase gate.
    zz_phase,
    /// ZZPhase gate with dynamic indices.
    zz_phase_d,
    /// CX gate.
    cx,
    /// CX gate with dynamic indices.
    cx_d,
    /// Swap of two qubits within a block.
    swap,
    /// Swap of two qubits within a block with dynamic indices.
    swap_d,
    /// ZZPhase gate involving two blocks.
    zz_phase_between_blocks,
    /// ZZPhase gate involving two blocks with dynamic indices.
    zz_phase_between_blocks_d,
    /// CX gate applied transversally over two blocks.
    cx_transversal,
    /// Prepare the all-zero state on a block.
    alloc_zero,
    /// Free a block.
    free,
    /// Syndrome measurement.
    measure_syndrome,
    /// Destructive measurement of all qubits.
    measure_all,
    /// Fallible non-destructive measurement of one qubit in the X basis.
    try_measure_one_x,
    /// Fallible non-destructive measurement of one qubit in the X basis with dynamic index.
    try_measure_one_x_d,
    /// Fallible non-destructive measurement of one qubit in the Z basis.
    try_measure_one_z,
    /// Fallible non-destructive measurement of one qubit in the Z basis with dynamic index.
    try_measure_one_z_d,
}

/// Concrete Iceberg logical operation with block size and indices set.
pub struct ConcreteIcebergOp {
    /// The kind of operation.
    pub def: IcebergOpDef,

    /// The block size.
    pub k: TypeArg,

    /// Qubit index parameters.
    pub indices: Vec<TypeArg>,
}

impl HasConcrete for IcebergOpDef {
    type Concrete = ConcreteIcebergOp;

    fn instantiate(&self, type_args: &[TypeArg]) -> Result<Self::Concrete, OpLoadError> {
        Ok(ConcreteIcebergOp {
            def: *self,
            k: type_args[0].clone(),
            indices: type_args[1..].to_vec(),
        })
    }
}

impl HasDef for ConcreteIcebergOp {
    type Def = IcebergOpDef;
}

impl MakeExtensionOp for ConcreteIcebergOp {
    fn op_id(&self) -> OpName {
        self.def.opdef_id()
    }

    fn from_extension_op(ext_op: &ExtensionOp) -> Result<Self, OpLoadError> {
        let def = IcebergOpDef::from_def(ext_op.def())?;
        def.instantiate(ext_op.args())
    }

    fn type_args(&self) -> Vec<TypeArg> {
        let mut args: Vec<TypeArg> = vec![self.k.clone()];
        args.extend(self.indices.iter().cloned());
        args
    }
}

impl MakeRegisteredOp for ConcreteIcebergOp {
    fn extension_id(&self) -> ExtensionId {
        EXTENSION_ID.clone()
    }

    fn extension_ref(&self) -> Arc<Extension> {
        EXTENSION.clone()
    }
}

impl IcebergOpDef {
    /// Initialize a [`ConcreteIcebergOp`] from an [`IcebergOpDef`] that
    /// requires a single qubit index.
    #[must_use]
    pub fn with_size_and_index(self, k: u64, i: u64) -> ConcreteIcebergOp {
        ConcreteIcebergOp {
            def: self,
            k: k.into(),
            indices: vec![i.into()],
        }
    }
}

/// Get an array-of-future-bool type with size corresponding to a type variable
/// with a given ID.
fn bool_array_tv(var_id: usize) -> Type {
    BorrowArray::ty_parametric(
        TypeArg::new_var_use(var_id, TypeParam::max_nat_type()),
        future_type(bool_t()),
    )
    .unwrap()
}

fn vec_of_blocks_and_angles(n_blocks: usize, n_angles: usize) -> Vec<Type> {
    let mut types: Vec<Type> = vec![block_tv(0); n_blocks];
    types.extend(vec![float64_type(); n_angles]);
    types
}

fn vec_of_blocks_and_ints_and_angles(
    n_blocks: usize,
    n_indices: usize,
    n_angles: usize,
) -> Vec<Type> {
    let mut types: Vec<Type> = vec![block_tv(0); n_blocks];
    types.extend(vec![int_type(6); n_indices]);
    types.extend(vec![float64_type(); n_angles]);
    types
}

/// A vector consisting of future-bool types followed by block types.
/// (Block types last because used as output row and guppylang expects this.)
fn vec_of_blocks_and_bools(n_blocks: usize, n_bools: usize) -> Vec<Type> {
    let mut types: Vec<Type> = vec![future_type(bool_t()); n_bools];
    types.extend(vec![block_tv(0); n_blocks]);
    types
}

fn optional_future_bool() -> Type {
    option_type(vec![future_type(bool_t())]).into()
}

/// A vector consisting of an optional-future-bool type followed by a block
/// type. (Block type last because used as output row and guppylang expects
/// this.)
fn block_and_optional_bool() -> Vec<Type> {
    vec![optional_future_bool(), block_tv(0)]
}

/// Signature of an operation that acts on a single block, with a number of
/// additional angle inputs and a number of index parameters.
fn sig_1_block(n_angles: usize, n_indices: usize) -> SignatureFunc {
    PolyFuncTypeRV::new(
        vec![TypeParam::max_nat_type(); 1 + n_indices],
        FuncValueType::new(
            vec_of_blocks_and_angles(1, n_angles),
            vec_of_blocks_and_angles(1, 0),
        ),
    )
    .into()
}

/// Signature of an operation that acts on a single block, with a number of
/// additional angle inputs and a number of index inputs.
fn sig_1_block_d(n_angles: usize, n_indices: usize) -> SignatureFunc {
    PolyFuncTypeRV::new(
        vec![TypeParam::max_nat_type()],
        FuncValueType::new(
            vec_of_blocks_and_ints_and_angles(1, n_indices, n_angles),
            vec_of_blocks_and_ints_and_angles(1, 0, 0),
        ),
    )
    .into()
}

impl MakeOpDef for IcebergOpDef {
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

    /// TODO use `CustomValidator` when defining op signatures
    /// See: <https://github.com/quantinuum-dev/guppyft/issues/82>
    fn init_signature(&self, _extension_ref: &Weak<Extension>) -> SignatureFunc {
        use IcebergOpDef::*;
        match self {
            x => sig_1_block(0, 1),
            x_d => sig_1_block_d(0, 1),
            z => sig_1_block(0, 1),
            z_d => sig_1_block_d(0, 1),
            xx => sig_1_block(0, 2),
            xx_d => sig_1_block_d(0, 2),
            yy => sig_1_block(0, 2),
            yy_d => sig_1_block_d(0, 2),
            zz => sig_1_block(0, 2),
            zz_d => sig_1_block_d(0, 2),
            all_but_one_x => sig_1_block(0, 1),
            all_but_one_x_d => sig_1_block_d(0, 1),
            all_but_one_z => sig_1_block(0, 1),
            all_but_one_z_d => sig_1_block_d(0, 1),
            all_x => sig_1_block(0, 0),
            all_y => sig_1_block(0, 0),
            all_z => sig_1_block(0, 0),
            x_with_all_but_one_z => sig_1_block(0, 1),
            x_with_all_but_one_z_d => sig_1_block_d(0, 1),
            z_with_all_but_one_x => sig_1_block(0, 1),
            z_with_all_but_one_x_d => sig_1_block_d(0, 1),
            fan_out => sig_1_block(0, 1),
            fan_out_d => sig_1_block_d(0, 1),
            fan_in => sig_1_block(0, 1),
            fan_in_d => sig_1_block_d(0, 1),
            rx => sig_1_block(1, 1),
            rx_d => sig_1_block_d(1, 1),
            rz => sig_1_block(1, 1),
            rz_d => sig_1_block_d(1, 1),
            all_rx => sig_1_block(1, 0),
            all_ry => sig_1_block(1, 0),
            all_rz => sig_1_block(1, 0),
            all_but_one_rx => sig_1_block(1, 1),
            all_but_one_rx_d => sig_1_block_d(1, 1),
            all_but_one_rz => sig_1_block(1, 1),
            all_but_one_rz_d => sig_1_block_d(1, 1),
            all_h => sig_1_block(0, 0),
            xx_phase => sig_1_block(1, 2),
            xx_phase_d => sig_1_block_d(1, 2),
            yy_phase => sig_1_block(1, 2),
            yy_phase_d => sig_1_block_d(1, 2),
            zz_phase => sig_1_block(1, 2),
            zz_phase_d => sig_1_block_d(1, 2),
            cx => sig_1_block(0, 2),
            cx_d => sig_1_block_d(0, 2),
            swap => sig_1_block(0, 2),
            swap_d => sig_1_block_d(0, 2),
            zz_phase_between_blocks => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type(); 3],
                FuncValueType::new(
                    vec_of_blocks_and_angles(2, 1),
                    vec_of_blocks_and_angles(2, 0),
                ),
            )
            .into(),
            zz_phase_between_blocks_d => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_ints_and_angles(2, 2, 1),
                    vec_of_blocks_and_ints_and_angles(2, 0, 0),
                ),
            )
            .into(),
            cx_transversal => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new_endo(vec_of_blocks_and_angles(2, 0)),
            )
            .into(),
            alloc_zero => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_angles(0, 0),
                    vec_of_blocks_and_angles(1, 0),
                ),
            )
            .into(),
            free => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_angles(1, 0),
                    vec_of_blocks_and_angles(0, 0),
                ),
            )
            .into(),
            measure_syndrome => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_angles(1, 0),
                    vec_of_blocks_and_bools(1, 2),
                ),
            )
            .into(),
            measure_all => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(vec_of_blocks_and_angles(1, 0), vec![bool_array_tv(0)]),
            )
            .into(),
            try_measure_one_x => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type(); 2],
                FuncValueType::new(vec_of_blocks_and_angles(1, 0), block_and_optional_bool()),
            )
            .into(),
            try_measure_one_x_d => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_ints_and_angles(1, 1, 0),
                    block_and_optional_bool(),
                ),
            )
            .into(),
            try_measure_one_z => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type(); 2],
                FuncValueType::new(vec_of_blocks_and_angles(1, 0), block_and_optional_bool()),
            )
            .into(),
            try_measure_one_z_d => PolyFuncTypeRV::new(
                vec![TypeParam::max_nat_type()],
                FuncValueType::new(
                    vec_of_blocks_and_ints_and_angles(1, 1, 0),
                    block_and_optional_bool(),
                ),
            )
            .into(),
        }
    }

    fn description(&self) -> String {
        self.get_variant_docs().into()
    }
}

/// Extension for logical Iceberg operations.
pub static EXTENSION: LazyLock<Arc<Extension>> = LazyLock::new(|| {
    Extension::new_arc(EXTENSION_ID, VERSION, |extension, extension_ref| {
        IcebergOpDef::load_all_ops(extension, extension_ref).unwrap();
    })
});

#[cfg(test)]
mod tests {
    use hugr::{
        CircuitUnit, HugrView, Wire,
        builder::{
            DFGBuilder, Dataflow, DataflowHugr, DataflowSubContainer, HugrBuilder, ModuleBuilder,
        },
        envelope::{EnvelopeConfig, EnvelopeFormat, read_envelope, write_envelope},
        extension::ExtensionRegistry,
        ops::DataflowOpTrait,
        package::Package,
        std_extensions::{
            arithmetic::{float_types::ConstF64, int_types::ConstInt},
            collections::borrow_array::borrow_array_type,
            std_reg,
        },
        types::Signature,
    };

    use crate::iceberg::types::EXTENSION as types_extension;
    use crate::iceberg::types::block_type;

    use super::*;

    #[test]
    fn test_iceberg_ops_extension() {
        assert_eq!(EXTENSION.name() as &str, "guppyft.iceberg.ops");
        assert_eq!(EXTENSION.types().count(), 0);
        assert_eq!(EXTENSION.operations().count(), 58);
    }

    #[test]
    fn test_signatures() {
        assert_eq!(
            IcebergOpDef::x
                .with_size_and_index(6, 3)
                .to_extension_op()
                .unwrap()
                .signature()
                .as_ref(),
            &Signature::new([block_type(6)], [block_type(6)])
        );
    }

    #[test]
    fn test_hugr_ops() {
        let block = block_type(6);
        let x3 = EXTENSION
            .instantiate_extension_op("x", [6.into(), 3.into()])
            .unwrap();
        let x_d = EXTENSION
            .instantiate_extension_op("x_d", [6.into()])
            .unwrap();
        let z4 = EXTENSION
            .instantiate_extension_op("z", [6.into(), 4.into()])
            .unwrap();
        let yy14 = EXTENSION
            .instantiate_extension_op("yy", [6.into(), 1.into(), 4.into()])
            .unwrap();
        let allx = EXTENSION
            .instantiate_extension_op("all_x", [6.into()])
            .unwrap();
        let allrz = EXTENSION
            .instantiate_extension_op("all_rz", [6.into()])
            .unwrap();
        let rz3 = EXTENSION
            .instantiate_extension_op("rz", [6.into(), 3.into()])
            .unwrap();
        let rx_d = EXTENSION
            .instantiate_extension_op("rx_d", [6.into()])
            .unwrap();
        let allbutonerz1 = EXTENSION
            .instantiate_extension_op("all_but_one_rz", [6.into(), 1.into()])
            .unwrap();
        let allh = EXTENSION
            .instantiate_extension_op("all_h", [6.into()])
            .unwrap();
        let yyphase05 = EXTENSION
            .instantiate_extension_op("yy_phase", [6.into(), 0.into(), 5.into()])
            .unwrap();
        let xxphase_d = EXTENSION
            .instantiate_extension_op("xx_phase_d", [6.into()])
            .unwrap();
        let zzphasebetweenblocks34 = EXTENSION
            .instantiate_extension_op("zz_phase_between_blocks", [6.into(), 3.into(), 4.into()])
            .unwrap();
        let zzphasebetweenblocks_d = EXTENSION
            .instantiate_extension_op("zz_phase_between_blocks_d", [6.into()])
            .unwrap();
        let cxtransverse = EXTENSION
            .instantiate_extension_op("cx_transversal", [6.into()])
            .unwrap();
        let cx23 = EXTENSION
            .instantiate_extension_op("cx", [6.into(), 2.into(), 3.into()])
            .unwrap();
        let cx_d = EXTENSION
            .instantiate_extension_op("cx_d", [6.into()])
            .unwrap();
        let swap51 = EXTENSION
            .instantiate_extension_op("swap", [6.into(), 5.into(), 1.into()])
            .unwrap();
        assert_eq!(x3.description(), "X gate.");
        assert_eq!(
            zzphasebetweenblocks_d.description(),
            "ZZPhase gate involving two blocks with dynamic indices."
        );
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block; 2]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(x3, [0]).unwrap();
        let index2 = linear.add_constant(ConstInt::new_u(6, 2).unwrap());
        let index5 = linear.add_constant(ConstInt::new_u(6, 5).unwrap());
        linear
            .append_and_consume(x_d, [CircuitUnit::Linear(0), CircuitUnit::Wire(index2)])
            .unwrap();
        linear.append(z4, [0]).unwrap();
        linear.append(yy14, [0]).unwrap();
        linear.append(allx, [0]).unwrap();
        let angle = linear.add_constant(ConstF64::new(0.25));
        linear
            .append_and_consume(allrz, [CircuitUnit::Linear(0), CircuitUnit::Wire(angle)])
            .unwrap();
        linear
            .append_and_consume(rz3, [CircuitUnit::Linear(0), CircuitUnit::Wire(angle)])
            .unwrap();
        linear
            .append_and_consume(
                rx_d,
                [
                    CircuitUnit::Linear(0),
                    CircuitUnit::Wire(index2),
                    CircuitUnit::Wire(angle),
                ],
            )
            .unwrap();
        linear
            .append_and_consume(
                allbutonerz1,
                [CircuitUnit::Linear(0), CircuitUnit::Wire(angle)],
            )
            .unwrap();
        linear.append(allh, [0]).unwrap();
        linear
            .append_and_consume(
                yyphase05,
                [CircuitUnit::Linear(0), CircuitUnit::Wire(angle)],
            )
            .unwrap();
        linear
            .append_and_consume(
                xxphase_d,
                [
                    CircuitUnit::Linear(0),
                    CircuitUnit::Wire(index2),
                    CircuitUnit::Wire(index5),
                    CircuitUnit::Wire(angle),
                ],
            )
            .unwrap();
        linear
            .append_and_consume(
                zzphasebetweenblocks34,
                [
                    CircuitUnit::Linear(0),
                    CircuitUnit::Linear(1),
                    CircuitUnit::Wire(angle),
                ],
            )
            .unwrap();
        linear
            .append_and_consume(
                zzphasebetweenblocks_d,
                [
                    CircuitUnit::Linear(0),
                    CircuitUnit::Linear(1),
                    CircuitUnit::Wire(index2),
                    CircuitUnit::Wire(index5),
                    CircuitUnit::Wire(angle),
                ],
            )
            .unwrap();
        linear.append(cxtransverse, [0, 1]).unwrap();
        linear.append(cx23, [1]).unwrap();
        linear
            .append_and_consume(
                cx_d,
                [
                    CircuitUnit::Linear(0),
                    CircuitUnit::Wire(index2),
                    CircuitUnit::Wire(index5),
                ],
            )
            .unwrap();
        linear.append(swap51, [0]).unwrap();
        let outs = linear.finish();
        f_build.finish_with_outputs(outs).unwrap();
        let h = module_builder.finish_hugr().unwrap();
        h.validate().unwrap();
    }

    #[test]
    fn test_alloc_measure_free() {
        let alloczero = EXTENSION
            .instantiate_extension_op("alloc_zero", [8.into()])
            .unwrap();
        let x3 = EXTENSION
            .instantiate_extension_op("x", [8.into(), 3.into()])
            .unwrap();
        let measuresyndrome = EXTENSION
            .instantiate_extension_op("measure_syndrome", [8.into()])
            .unwrap();
        let free = EXTENSION
            .instantiate_extension_op("free", [8.into()])
            .unwrap();
        let outputs: Vec<Type> = vec![future_type(bool_t()); 2];
        let mut dfg_builder = DFGBuilder::new(Signature::new(vec![], outputs)).unwrap();
        let handle = dfg_builder.add_dataflow_op(alloczero, vec![]).unwrap();
        let handle = dfg_builder.add_dataflow_op(x3, handle.outputs()).unwrap();
        let handle = dfg_builder
            .add_dataflow_op(measuresyndrome, handle.outputs())
            .unwrap();
        let wires: Vec<Wire> = handle.outputs().collect();
        assert_eq!(wires.len(), 3);
        let bool_wire_0 = wires[0];
        let bool_wire_1 = wires[1];
        let block_wire = wires[2];
        let handle = dfg_builder.add_dataflow_op(free, [block_wire]).unwrap();
        let outs: Vec<Wire> = handle.outputs().collect();
        assert!(outs.is_empty());
        let h = dfg_builder
            .finish_hugr_with_outputs([bool_wire_0, bool_wire_1])
            .unwrap();
        h.validate().unwrap();
    }

    #[test]
    fn test_measure_all() {
        let measureall = EXTENSION
            .instantiate_extension_op("measure_all", [4.into()])
            .unwrap();
        let mut dfg_builder = DFGBuilder::new(Signature::new(
            [block_type(4)],
            [borrow_array_type(4, future_type(bool_t()))],
        ))
        .unwrap();
        let handle = dfg_builder
            .add_dataflow_op(measureall, dfg_builder.input_wires())
            .unwrap();
        let h = dfg_builder
            .finish_hugr_with_outputs(handle.outputs())
            .unwrap();
        h.validate().unwrap();
    }

    #[test]
    fn test_measure_one() {
        let measureonez0 = EXTENSION
            .instantiate_extension_op("try_measure_one_z", [2.into(), 0.into()])
            .unwrap();
        let measureonez1 = EXTENSION
            .instantiate_extension_op("try_measure_one_z", [2.into(), 1.into()])
            .unwrap();
        let measureonez_d = EXTENSION
            .instantiate_extension_op("try_measure_one_z_d", [2.into()])
            .unwrap();
        let allh = EXTENSION
            .instantiate_extension_op("all_h", [2.into()])
            .unwrap();
        let mut dfg_builder = DFGBuilder::new(Signature::new(
            vec![block_type(2)],
            vec![
                block_type(2),
                optional_future_bool(),
                optional_future_bool(),
                optional_future_bool(),
            ],
        ))
        .unwrap();
        let handle = dfg_builder
            .add_dataflow_op(allh, dfg_builder.input_wires())
            .unwrap();
        let handle = dfg_builder
            .add_dataflow_op(measureonez0, handle.outputs())
            .unwrap();
        let [maybe_c0, block] = handle.outputs_arr();
        let handle = dfg_builder
            .add_dataflow_op(measureonez1, vec![block])
            .unwrap();
        let [maybe_c1, block] = handle.outputs_arr();
        let index0_wire = dfg_builder.add_load_value(ConstInt::new_u(6, 0).unwrap());
        let handle = dfg_builder
            .add_dataflow_op(measureonez_d, [block, index0_wire])
            .unwrap();
        let [maybe_c2, block] = handle.outputs_arr();
        let h = dfg_builder
            .finish_hugr_with_outputs(vec![block, maybe_c0, maybe_c1, maybe_c2])
            .unwrap();
        h.validate().unwrap();
    }

    #[test]
    fn test_serialization() {
        let block = block_type(6);
        let x3 = EXTENSION
            .instantiate_extension_op("x", [6.into(), 3.into()])
            .unwrap();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(x3, [0]).unwrap();
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

    #[test]
    fn test_mismatched_k() {
        let block = block_type(6);
        let x3 = EXTENSION
            .instantiate_extension_op("x", [6.into(), 3.into()])
            .unwrap();
        let x3_bad_k = EXTENSION
            .instantiate_extension_op("x", [4.into(), 3.into()])
            .unwrap();
        let mut module_builder = ModuleBuilder::new();
        let signature = Signature::new_endo(vec![block]);
        let mut f_build = module_builder.define_function("main", signature).unwrap();
        let wires: Vec<_> = f_build.input_wires().collect();
        let mut linear = f_build.as_circuit(wires);
        linear.append(x3, [0]).unwrap();
        linear.append(x3_bad_k, [0]).unwrap();
        let outs = linear.finish();
        f_build.finish_with_outputs(outs).unwrap();
        assert!(module_builder.finish_hugr().is_err());
    }
}
