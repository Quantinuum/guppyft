//! Minimal computational-to-CSD lowering: one computational qubit per block.
//!
//! In data blocks, slot 0 holds the computational state and slot 1 stays in zero.
//! T injections allocate and consume separate magic-state blocks. The input must
//! already be decomposed into the Clifford+T operations handled below.

use std::error::Error;

use extensions::csd;
use hugr::{
    Hugr, HugrView, Wire,
    builder::{BuildError, DFGBuilder, Dataflow, DataflowHugr},
    extension::prelude::{bool_t, qb_t},
    ops::{DataflowOpTrait, ExtensionOp},
    types::{Transformable, TypeArg},
};
use itertools::Itertools;
use tket::{
    extension::measurement::measurement_custom_type,
    passes::{
        ComposablePass, ReplaceTypes,
        replace_types::{NodeTemplate, handlers::register_linear_array_op_replacements},
    },
};

/// Compile a computational HUGR in place, using only logical slot 0 of each block.
///
/// Classical control flow is retained, including measurement-dependent retries.
/// Returned qubits become returned blocks; this pass does not measure them.
pub fn compile(hugr: &mut Hugr) -> Result<(), Box<dyn Error>> {
    let mut replacements = ReplaceTypes::default();
    replacements.set_replace_type(qb_t().as_extension().unwrap().clone(), csd::block_type());
    replacements.set_replace_type(measurement_custom_type(), bool_t());

    // Rewrite array operations as well as their element types. Branches, loops,
    // tuples and function signatures are handled by ReplaceTypes itself.
    register_linear_array_op_replacements(&mut replacements);

    let source_ops = hugr
        .nodes()
        .filter_map(|node| hugr.get_optype(node).as_extension_op())
        .filter(|op| {
            matches!(
                op.def().extension_id().as_ref(),
                "tket.quantum" | "tket.measurement"
            )
        })
        .unique_by(|op| op.qualified_id());

    for op in source_ops {
        let body = lower_op(op, &replacements)?;
        replacements.set_replace_op(op, NodeTemplate::linked_hugr(body));
    }

    // TODO: Diagnose unsupported quantum extensions and signatures before mutation.
    // TODO: Attach source-node context to errors and preserve the input on failure.
    replacements.run(hugr)?;
    hugr.validate()?;
    Ok(())
}

fn lower_op(op: &ExtensionOp, replacements: &ReplaceTypes) -> Result<Hugr, Box<dyn Error>> {
    let mut signature = op.signature().into_owned();
    signature.transform(replacements)?;
    let mut builder = DFGBuilder::new(signature)?;
    let inputs: Vec<_> = builder.input_wires().collect();

    // These input positions assume the standard TKET signatures.
    // TODO: Report malformed signatures explicitly instead of relying on indexing.
    let outputs = match op.def().name().as_str() {
        "QAlloc" => add_gate::<1>(&mut builder, "prep_zero", &[], [])?.to_vec(),
        "H" => add_gate::<1>(&mut builder, "targeted_h", &[0], inputs)?.to_vec(),
        "T" | "Tdg" | "S" | "Sdg" | "Z" => {
            // Simple exact phase-gate identities; dedicated ops could reduce cost.
            let count = match op.def().name().as_str() {
                "T" => 1,
                "S" => 2,
                "Z" => 4,
                "Sdg" => 6,
                "Tdg" => 7,
                _ => unreachable!(),
            };
            vec![phase(&mut builder, inputs[0], count)?]
        }
        "X" => {
            // H Z H implements X on slot 0 while leaving slot 1 in zero.
            let [block] = add_gate(&mut builder, "targeted_h", &[0], inputs)?;
            let block = phase(&mut builder, block, 4)?;
            add_gate::<1>(&mut builder, "targeted_h", &[0], [block])?.to_vec()
        }
        "CX" => add_gate::<2>(&mut builder, "targeted_cnot", &[0, 0], inputs)?.to_vec(),
        "CZ" => {
            let [target] = add_gate(&mut builder, "targeted_h", &[0], [inputs[1]])?;
            let [control, target] =
                add_gate(&mut builder, "targeted_cnot", &[0, 0], [inputs[0], target])?;
            let [target] = add_gate(&mut builder, "targeted_h", &[0], [target])?;
            vec![control, target]
        }
        "Measure" => add_gate::<2>(&mut builder, "targeted_measure_z", &[0], inputs)?.to_vec(),
        "MeasureFree" | "QFree" => {
            // Consume the whole block; slot 1 has no computational result to retain.
            let [result, _unused] = add_gate(&mut builder, "measure_z", &[], inputs)?;
            if op.def().name().as_str() == "MeasureFree" {
                vec![result]
            } else {
                vec![]
            }
        }
        // CSD measurement already returns bool, so the old measurement Read is identity.
        "Read" => inputs,
        // TODO: Replace this generic error with a diagnostic listing supported gates.
        _ => return Err(format!("Unsupported CSD input operation: {}", op.qualified_id()).into()),
    };
    Ok(builder.finish_hugr_with_outputs(outputs)?)
}

fn phase(builder: &mut impl Dataflow, mut block: Wire, count: usize) -> Result<Wire, BuildError> {
    for _ in 0..count {
        // Each injection consumes a fresh resource block; data stays in slot 0.
        let [magic] = add_gate(builder, "prep_magic_state", &[], [])?;
        [block] = add_gate(builder, "targeted_t", &[0], [block, magic])?;
    }
    Ok(block)
}

fn add_gate<const N: usize>(
    builder: &mut impl Dataflow,
    name: &str,
    indices: &[u64],
    inputs: impl IntoIterator<Item = Wire>,
) -> Result<[Wire; N], BuildError> {
    let args: Vec<_> = indices.iter().copied().map(TypeArg::from).collect();
    let op = csd::EXTENSION.instantiate_extension_op(name, args)?;
    Ok(builder.add_dataflow_op(op, inputs)?.outputs_arr())
}
