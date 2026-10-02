//! Minimal computational-to-CSD lowering using one logical qubit per input qubit.
//!
//! Single-qubit preparations and destructive measurements avoid spare wires.
//! T injections each prepare and consume a full magic pair. Physical block packing
//! is left to the downstream pipeline. The input must already be decomposed into
//! the Clifford+T operations handled below.

use std::error::Error;

use extensions::csd;
use hugr::{
    Hugr, HugrView, Wire,
    builder::{BuildError, DFGBuilder, Dataflow, DataflowHugr},
    extension::prelude::{bool_t, qb_t},
    ops::{DataflowOpTrait, ExtensionOp},
    types::Transformable,
};
use itertools::Itertools;
use tket::{
    extension::measurement::measurement_custom_type,
    passes::{
        ComposablePass, ReplaceTypes,
        replace_types::{NodeTemplate, handlers::register_linear_array_op_replacements},
    },
};

/// Compile a computational HUGR in place, using one CSD logical qubit per qubit.
///
/// Classical control flow is retained, including measurement-dependent retries.
/// Returned qubits remain live logical qubits; this pass does not measure them.
pub fn compile(hugr: &mut Hugr) -> Result<(), Box<dyn Error>> {
    let mut replacements = ReplaceTypes::default();
    replacements.set_replace_type(
        qb_t().as_extension().unwrap().clone(),
        csd::logical_qubit_type(),
    );
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
        "QAlloc" => add_gate::<1>(&mut builder, "prep_zero_single", [])?.to_vec(),
        "H" => add_gate::<1>(&mut builder, "targeted_h", inputs)?.to_vec(),
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
            // H Z H implements X without introducing any other data qubits.
            let [qubit] = add_gate(&mut builder, "targeted_h", inputs)?;
            let qubit = phase(&mut builder, qubit, 4)?;
            add_gate::<1>(&mut builder, "targeted_h", [qubit])?.to_vec()
        }
        "CX" => add_gate::<2>(&mut builder, "targeted_cnot", inputs)?.to_vec(),
        "CZ" => {
            let [target] = add_gate(&mut builder, "targeted_h", [inputs[1]])?;
            let [control, target] = add_gate(&mut builder, "targeted_cnot", [inputs[0], target])?;
            let [target] = add_gate(&mut builder, "targeted_h", [target])?;
            vec![control, target]
        }
        "Measure" => add_gate::<2>(&mut builder, "targeted_measure_z", inputs)?.to_vec(),
        "MeasureFree" | "QFree" => {
            // The logical qubit is consumed; only the copyable result may be discarded.
            let [result] = add_gate(&mut builder, "measure_z_single", inputs)?;
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

fn phase(builder: &mut impl Dataflow, mut qubit: Wire, count: usize) -> Result<Wire, BuildError> {
    for _ in 0..count {
        // Magic resources are prepared and consumed as a pair, even for one data qubit.
        let [magic] = add_gate(builder, "prep_magic_state", [])?;
        [qubit] = add_gate(builder, "targeted_t", [qubit, magic])?;
    }
    Ok(qubit)
}

fn add_gate<const N: usize>(
    builder: &mut impl Dataflow,
    name: &str,
    inputs: impl IntoIterator<Item = Wire>,
) -> Result<[Wire; N], BuildError> {
    let op = csd::EXTENSION.instantiate_extension_op(name, [])?;
    Ok(builder.add_dataflow_op(op, inputs)?.outputs_arr())
}
