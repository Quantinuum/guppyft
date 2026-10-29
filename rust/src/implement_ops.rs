//! The implement pass for replacing operations with function implementations.

#![allow(missing_docs)]

use anyhow::Context;
use hugr::{
    Hugr, HugrView, Node,
    builder::{BuildError, HugrBuilder, ModuleBuilder},
    extension::{ExtensionId, SignatureError, prelude::MakeTuple},
    hugr::{ValidationError, hugrmut::HugrMut},
    ops::{Call, DataflowOpTrait, ExtensionOp, Input, OpName, OpType, handle::NodeHandle},
    types::{PolyFuncType, Type, TypeRow},
};
use hugr_core::hugr::internal::HugrMutInternals;
use hugr_core::hugr::linking::NodeLinkingError;
use hugr_core::std_extensions::arithmetic::float_types::float64_type;
use hugr_core::std_extensions::collections::array::Array;
use hugr_core::std_extensions::collections::borrow_array::BorrowArray;
use hugr_core::types::{CustomType, SumType, Transformable, TypeArg, TypeName};
use hugr_core::{Direction, OutgoingPort, PortIndex, Visibility};
use itertools::Itertools;
use std::collections::{BTreeMap, HashMap, HashSet, hash_map::Entry};
use tket::extension::rotation::{RotationOp, rotation_type};
use tket::passes::replace_types::handlers::register_linear_array_op_replacements;
use tket::passes::utils::unpack_container::type_unpack::array_args;
use tket::passes::{
    ComposablePass, PassScope, ReplaceTypes, WithScope, replace_types::ReplaceTypesError,
};

#[derive(derive_more::Error, Debug, derive_more::Display, derive_more::From)]
#[non_exhaustive]
pub enum ImplementOpsPassError {
    #[from]
    OpReplacementError(OpReplacementError),
    #[from]
    ValidationError(ValidationError<Node>),
    #[from(SignatureError, BuildError)]
    BuildError(BuildError),
    #[display("Type replacement mismatch error. src: {src}, first: {first}, second: {second}.")]
    InconsistentTypeReplacement {
        src: Box<CustomType>,
        first: Box<Type>,
        second: Box<Type>,
    },
    MissingFunctionHugr {
        name: String,
    },
}

pub type OpId = (String, String);
pub type TypeId = (String, String);
pub type OpReplacements = BTreeMap<OpId, (Option<Hugr>, String)>;

#[derive(Debug, Clone, Default)]
pub struct ImplementOpsPass {
    scope: PassScope,
    pub op_replacements: OpReplacements,
    replaceable_types: HashSet<(ExtensionId, TypeName)>,
    check_eliminated: HashSet<ExtensionId>,
    adapt_rotation_inputs: bool,
}

impl ImplementOpsPass {
    pub fn new(
        op_replacements: OpReplacements,
        ty_replacements: HashSet<(ExtensionId, TypeName)>,
        check_eliminated: HashSet<ExtensionId>,
        adapt_rotation_inputs: bool,
    ) -> Self {
        Self {
            op_replacements,
            replaceable_types: ty_replacements,
            check_eliminated,
            adapt_rotation_inputs,
            ..Self::default()
        }
    }

    fn check_all_ops_eliminated<H: HugrView<Node = Node>>(&self, hugr: &H) -> anyhow::Result<()> {
        if !self
            .check_eliminated
            .iter()
            .any(|ext_id| hugr.extensions().contains(ext_id))
        {
            return Ok(());
        }

        for node in hugr.nodes() {
            let Some(ext_op) = hugr.get_optype(node).as_extension_op() else {
                continue;
            };
            let ext_id = ext_op.def().extension_id();
            if self.check_eliminated.contains(ext_id) {
                return Err(anyhow::anyhow!(
                    "Extension {ext_id} was requested to be eliminated but {} at node {node} remains",
                    ext_op.qualified_id()
                ));
            }
        }
        Ok(())
    }
}

impl WithScope for ImplementOpsPass {
    fn with_scope(mut self, scope: impl Into<PassScope>) -> Self {
        self.scope = scope.into();
        self
    }
}

#[derive(Debug, derive_more::Display, derive_more::From)]
pub struct ImplementOpsError(anyhow::Error);

impl std::error::Error for ImplementOpsError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        self.0.source()
    }
}

impl<H: HugrMut<Node = Node> + AsMut<Hugr>> ComposablePass<H> for ImplementOpsPass {
    type Error = ImplementOpsError;
    type Result = ();

    fn run(&self, hugr: &mut H) -> Result<Self::Result, Self::Error> {
        self.run_impl(hugr).map_err(Into::into)
    }
}

impl ImplementOpsPass {
    fn run_impl<H: HugrMut<Node = Node> + AsMut<Hugr>>(
        &self,
        hugr: &mut H,
    ) -> Result<(), anyhow::Error> {
        #[cfg(debug_assertions)]
        {
            for ext_op in hugr
                .nodes()
                .filter_map(|n| hugr.get_optype(n).as_extension_op())
            {
                let ext_name = ext_op.def().extension_id().to_string();
                let op_name = ext_op.def().name().to_string();
                let in_rewrite_ops = self
                    .op_replacements
                    .contains_key(&(ext_name.clone(), op_name.clone()));
                let in_extensions = hugr.extensions().get(&ext_name).is_some();
                assert!(
                    !in_rewrite_ops || in_extensions,
                    "Extension op '{ext_name}.{op_name}' found in `rewrite_ops` but not in hugr extension registry."
                );
            }
        }

        let op_funcs: Vec<(ExtensionOp, Option<Hugr>, &str)> = hugr
            .nodes()
            .filter_map(|n| hugr.get_optype(n).as_extension_op())
            .unique_by(|&op| OpHashWrapper::from(op))
            .filter_map(|ext_op| {
                let key = (
                    ext_op.def().extension_id().to_string(),
                    ext_op.def().name().to_string(),
                );
                let (func_hugr, func_name) = self.op_replacements.get(&key)?;
                Some((ext_op.clone(), func_hugr.clone(), func_name.as_str()))
            })
            .collect_vec();

        // Determine type replacements from differences between the `ext_op` and `func_hugr` signatures.
        // Filter using `self.ty_replacements` to only replace specific extension types.
        let type_map: HashMap<CustomType, Type> = op_funcs
            .iter()
            .try_fold(
                HashMap::new(),
                |mut map, (ext_op, func_hugr, func_name)| -> anyhow::Result<_> {
                    let func_hugr =
                        func_hugr
                            .as_ref()
                            .ok_or(ImplementOpsPassError::MissingFunctionHugr {
                                name: func_name.to_string(),
                            })?;

                    let src_sig = ext_op.signature();
                    let tgt_node = extract_func_node(func_hugr, func_name).ok_or(
                        ImplementOpsPassError::MissingFunctionHugr {
                            name: func_name.to_string(),
                        },
                    )?;
                    let Some(tgt_sig) = extract_func_sig(func_hugr, tgt_node) else {
                        unreachable!()
                    };
                    let tgt_sig = tgt_sig.instantiate(&[])?;

                    // Iterate through all types in the signature, recursively unpack both `src` and `tgt`
                    // to check if `src` is in `ty_replacements` and then use corresponding `tgt` type
                    // as the replacement.
                    for (src_ty, tgt_ty) in src_sig
                        .input
                        .iter()
                        .zip(tgt_sig.input.iter())
                        .chain(src_sig.output.iter().zip(tgt_sig.output.iter()))
                    {
                        let mut pending = vec![(src_ty.clone(), tgt_ty.clone())];
                        while let Some((src, tgt)) = pending.pop() {
                            if src == tgt {
                                continue;
                            }
                            if let Some(src_ct) = src.as_extension().cloned() {
                                let key = (src_ct.extension().clone(), src_ct.name().clone());
                                if self.replaceable_types.contains(&key) {
                                    insert_type_mapping(&mut map, src_ct, tgt)?;
                                    continue;
                                }
                            }

                            let (Some(src_children), Some(tgt_children)) =
                                (unpack_type(&src), unpack_type(&tgt))
                            else {
                                continue;
                            };

                            if src_children.len() != tgt_children.len() {
                                continue;
                            }

                            pending.extend(src_children.into_iter().zip(tgt_children));
                        }
                    }

                    Ok(map)
                },
            )
            .context("Could not build type replacement map")?;

        let mut state = OpReplacer::new_with_types(hugr, type_map, self.adapt_rotation_inputs);
        for (ext_op, func_hugr, func_name) in op_funcs {
            state
                .register_replacement(&ext_op, func_hugr, func_name)
                .context(format!(
                    "Could not register op replacement for {}",
                    ext_op.qualified_id()
                ))?;
        }
        state.finish().context("Could not finish op replacements")?;
        self.check_all_ops_eliminated(hugr)
            .context("Could not check requested extensions are eliminated")?;
        hugr.validate()
            .context("Could not validate hugr after replacement")?;
        Ok(())
    }
}

fn extract_func_node(func_hugr: &Hugr, func_name: &str) -> Option<Node> {
    func_hugr
        .children(func_hugr.module_root())
        .find(|node| match &func_hugr.get_optype(*node) {
            OpType::FuncDecl(decl) => decl.func_name() == func_name,
            OpType::FuncDefn(defn) => defn.func_name() == func_name,
            _ => false,
        })
}

fn unpack_type(ty: &Type) -> Option<Vec<Type>> {
    if let Some(row) = ty
        .as_sum()
        .and_then(|sum_type| SumType::as_tuple(sum_type).or_else(|| SumType::as_option(sum_type)))
    {
        Some(
            TypeRow::try_from(row.clone())
                .expect("unexpected row variable.")
                .into_owned(),
        )
    } else if let Some((size, elem_ty)) = ty
        .as_extension()
        .and_then(|ext| array_args::<Array>(ext).or_else(|| array_args::<BorrowArray>(ext)))
    {
        Some(vec![elem_ty; size as usize])
    } else {
        None
    }
}

fn insert_type_mapping(
    map: &mut HashMap<CustomType, Type>,
    src: CustomType,
    tgt: Type,
) -> Result<(), ImplementOpsPassError> {
    match map.entry(src) {
        Entry::Vacant(v) => {
            v.insert(tgt);
            Ok(())
        }
        Entry::Occupied(o) if o.get() == &tgt => Ok(()),
        Entry::Occupied(o) => Err(ImplementOpsPassError::InconsistentTypeReplacement {
            src: Box::new(o.key().clone()),
            first: Box::new(o.get().clone()),
            second: Box::new(tgt),
        }),
    }
}

fn extract_func_sig(func_hugr: &Hugr, node: Node) -> Option<PolyFuncType> {
    match &func_hugr.get_optype(node) {
        OpType::FuncDecl(decl) => Some(decl.signature().clone()),
        OpType::FuncDefn(defn) => Some(defn.signature().clone()),
        _ => None,
    }
}

/// Preprocess a replacement body to accept rotations at its entry instead of Guppy angles.
/// Declarations and signatures with any other mismatch are left unchanged.
fn preprocess_rotation_inputs(func_hugr: &mut Hugr, func_node: Node, expected_sig: &PolyFuncType) {
    let OpType::FuncDefn(defn) = func_hugr.get_optype(func_node) else {
        return;
    };
    let mut defn = defn.clone();
    let func_sig = defn.signature_mut();
    if !expected_sig.params().is_empty() || !func_sig.params().is_empty() {
        return;
    }
    let rotation_ty = rotation_type();
    let angle_ty = Type::new_tuple([float64_type()]);
    let rotation_inputs = expected_sig
        .body()
        .input
        .iter()
        .zip(func_sig.body_mut().input.iter_mut())
        .enumerate()
        .filter_map(|(index, (expected, found))| {
            if expected == &rotation_ty && *found == angle_ty {
                *found = rotation_ty.clone();
                Some(index)
            } else {
                None
            }
        })
        .collect_vec();
    if rotation_inputs.is_empty() || func_sig != expected_sig {
        return;
    }

    let [input, _] = func_hugr.get_io(func_node).expect("function has I/O nodes");
    func_hugr.replace_op(
        input,
        Input {
            types: func_sig.body().input.clone(),
        },
    );
    func_hugr.replace_op(func_node, defn);

    let to_halfturns: OpType = RotationOp::to_halfturns.into();
    let make_tuple: OpType = MakeTuple::new([float64_type()].into()).into();
    func_hugr.use_extensions(
        to_halfturns
            .used_extensions()
            .expect("rotation conversion extensions are available"),
    );
    func_hugr.use_extensions(
        make_tuple
            .used_extensions()
            .expect("tuple extensions are available"),
    );
    for index in rotation_inputs {
        let port = OutgoingPort::from(index);
        let consumers = func_hugr.linked_inputs(input, port).collect_vec();
        let halfturns = func_hugr.add_node_with_parent(func_node, to_halfturns.clone());
        let angle = func_hugr.add_node_with_parent(func_node, make_tuple.clone());
        func_hugr.disconnect(input, port);
        func_hugr.connect(input, port, halfturns, 0);
        func_hugr.connect(halfturns, 0, angle, 0);
        for (consumer, consumer_port) in consumers {
            func_hugr.connect(angle, 0, consumer, consumer_port);
        }
    }
}

#[derive(Clone, Hash, PartialEq, Eq)]
struct OpHashWrapper {
    op_name: String,
    args: Vec<TypeArg>,
}

impl From<&ExtensionOp> for OpHashWrapper {
    fn from(op: &ExtensionOp) -> Self {
        Self {
            op_name: op.qualified_id().to_string(),
            args: op.args().to_vec(),
        }
    }
}

#[derive(derive_more::Error, Debug, derive_more::Display, derive_more::From)]
#[non_exhaustive]
pub enum OpReplacementError {
    #[from]
    ReplaceTypesError(ReplaceTypesError),
    #[from]
    ValidationError(ValidationError<Node>),
    #[from(SignatureError, BuildError)]
    BuildError(BuildError),
    #[display(
        "Existing function '{name}' node {node} does not have the expected signature for op '{op_id}'. Expected: {expected}. Found {found}"
    )]
    ExistingFunctionSignatureMismatch {
        op_id: OpName,
        node: Node,
        name: String,
        expected: Box<PolyFuncType>,
        found: Box<PolyFuncType>,
    },
    #[from]
    NodeLinkingError(NodeLinkingError<Node, Node>),
    MissingFunctionHugr {
        name: String,
    },
}

pub(crate) struct OpReplacer<'a, H: HugrMut<Node = Node>> {
    hugr: &'a mut H,
    type_replacer: ReplaceTypes,
    op_calls: HashMap<OpHashWrapper, (OpType, Hugr, Node)>,
    adapt_rotation_inputs: bool,
}

impl<'a, H: HugrMut<Node = Node>> OpReplacer<'a, H> {
    pub fn new(hugr: &'a mut H, replacer: ReplaceTypes, adapt_rotation_inputs: bool) -> Self {
        Self {
            hugr,
            type_replacer: replacer,
            op_calls: Default::default(),
            adapt_rotation_inputs,
        }
    }

    pub fn new_with_types(
        hugr: &'a mut H,
        types: HashMap<CustomType, Type>,
        adapt_rotation_inputs: bool,
    ) -> Self {
        let mut type_replacer = ReplaceTypes::default();
        for (src, tgt) in types {
            type_replacer.set_replace_type(src, tgt);
        }

        register_linear_array_op_replacements(&mut type_replacer);

        Self::new(hugr, type_replacer, adapt_rotation_inputs)
    }

    fn get_func_node(
        &self,
        op_id: OpName,
        expected_sig: PolyFuncType,
        func_hugr: &mut Hugr,
        func_name: &str,
    ) -> Result<Node, OpReplacementError> {
        // Extract target function
        let func_node = extract_func_node(func_hugr, func_name).ok_or(
            OpReplacementError::MissingFunctionHugr {
                name: func_name.to_string(),
            },
        )?;
        if self.adapt_rotation_inputs {
            preprocess_rotation_inputs(func_hugr, func_node, &expected_sig);
        }
        let func_sig = extract_func_sig(func_hugr, func_node).expect("replacement is a function");

        if func_sig != expected_sig {
            return Err(OpReplacementError::ExistingFunctionSignatureMismatch {
                op_id,
                node: func_node,
                name: func_name.to_string(),
                expected: Box::new(expected_sig),
                found: Box::new(func_sig),
            });
        };

        Ok(func_node)
    }

    pub fn register_replacement(
        &mut self,
        ext_op: &ExtensionOp,
        func_hugr_opt: Option<Hugr>,
        func_name: &str,
    ) -> anyhow::Result<()> {
        let op_hash = OpHashWrapper::from(ext_op);
        if self.op_calls.contains_key(&op_hash) {
            return Ok(());
        }

        let expected_sig: PolyFuncType = {
            let mut sig = ext_op.signature().into_owned();
            sig.transform(&self.type_replacer)?;
            sig.into()
        };

        // Extract function if given, otherwise generate a declaration with the expected signature.
        let (func_hugr, func_node) = if let Some(mut hugr) = func_hugr_opt {
            let node =
                self.get_func_node(ext_op.qualified_id(), expected_sig, &mut hugr, func_name)?;
            (hugr, node)
        } else {
            let mut module_builder = ModuleBuilder::new();
            let decl = module_builder.declare(func_name, expected_sig)?;
            (module_builder.finish_hugr()?, decl.node())
        };

        // Register call for later replacement
        let call_type: OpType = Call::try_new((*ext_op.signature()).clone().into(), [])?.into();
        self.op_calls
            .insert(op_hash, (call_type, func_hugr, func_node));

        Ok(())
    }

    pub fn finish(mut self) -> anyhow::Result<()>
    where
        H: AsMut<Hugr>,
    {
        // In an optimal scenario we would use the type replacer to insert the function alongside
        // a call. However, since there is no way to stop the type replacer from recursively
        // processing the RHS at the moment, we have to resort to this hacky approach of manually
        // merging the func_hugr into the main hugr, and manually creating calls to the inserted
        // function.

        let ops_to_replace = self
            .hugr
            .nodes()
            .filter_map(|n| {
                self.hugr
                    .get_optype(n)
                    .as_extension_op()
                    .map(|op| (n, OpHashWrapper::from(op)))
            })
            .filter(|(_, hash)| self.op_calls.contains_key(hash))
            .collect_vec();

        // Transform all ops into calls, but don't link them yet. Add static port for connecting the
        // function later, since extension ops do not have static in-ports but calls do.
        for (node, hash) in ops_to_replace.iter() {
            let orig_optype = self.hugr.get_optype(*node);
            let new_port_index = orig_optype
                .other_input_port()
                .map(|p| p.index())
                .unwrap_or(orig_optype.input_count());
            *self.hugr.optype_mut(*node) = self.op_calls[hash].0.clone();
            self.hugr
                .insert_ports(*node, Direction::Incoming, new_port_index, 1);
        }

        // Transform signatures
        self.type_replacer.run(&mut self.hugr)?;

        // Insert all registered HUGRs after signature transform, so their contents are not affected
        let inserted_func_nodes: HashMap<OpHashWrapper, H::Node> = self
            .op_calls
            .into_iter()
            .map(|(op_hash, (_, mut func_hugr, func_node))| {
                let children = func_hugr
                    .children(func_hugr.module_root())
                    .map(|n| (n, self.hugr.module_root()))
                    .collect_vec();
                for (child, _) in &children {
                    let OpType::FuncDefn(defn) = func_hugr.get_optype(*child) else {
                        continue;
                    };
                    let mut defn = defn.clone();
                    *defn.visibility_mut() = Visibility::Private;
                    func_hugr.replace_op(*child, defn);
                }
                let inserted_func_node = *self
                    .hugr
                    .insert_forest(func_hugr, children)
                    .unwrap()
                    .node_map
                    .get(&func_node)
                    .unwrap_or_else(|| {
                        panic!(
                            "Could not find inserted function node for op: {}",
                            op_hash.op_name
                        )
                    });
                (op_hash, inserted_func_node)
            })
            .collect();

        // Connect calls for all instances of ops that should be replaced
        for (node, op_hash) in ops_to_replace {
            let func_node = inserted_func_nodes.get(&op_hash).unwrap();
            let func_port = self.hugr.num_outputs(*func_node) - 1;
            let call_in_port = self.hugr.get_optype(node).static_input_port().unwrap();
            self.hugr.connect(*func_node, func_port, node, call_in_port);
        }

        let registry = self.hugr.extensions().clone();
        self.hugr
            .as_mut()
            .resolve_extension_defs(&registry)
            .context("Could not resolve extensions after replacing ops")?;

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hugr::builder::{Container, Dataflow, DataflowSubContainer, FunctionBuilder};
    use hugr::envelope::EnvelopeConfig;
    use hugr::extension::prelude::{qb_t, usize_t};
    use hugr::types::{Signature, type_param::TypeParam};

    fn replacement_hugr(
        signature: PolyFuncType,
        output_inputs: &[usize],
    ) -> anyhow::Result<(Hugr, Node)> {
        let mut module = ModuleBuilder::new();
        let function = FunctionBuilder::with_hugr(module.hugr_mut(), "impl", signature)?;
        let args = function.input_wires().collect_vec();
        let node = function
            .finish_with_outputs(output_inputs.iter().map(|&index| args[index]))?
            .node();
        Ok((module.finish_hugr()?, node))
    }

    #[test]
    fn rotation_inputs_are_adapted_in_replacement_bodies() -> anyhow::Result<()> {
        let angle = Type::new_tuple([float64_type()]);
        let expected: PolyFuncType = Signature::new(
            [rotation_type(), qb_t(), angle.clone(), rotation_type()],
            [
                qb_t(),
                angle.clone(),
                angle.clone(),
                angle.clone(),
                angle.clone(),
            ],
        )
        .into();
        let extension = hugr::Extension::new_arc(
            ExtensionId::new_unchecked("test"),
            hugr::extension::Version::new(0, 1, 0),
            |extension, extension_ref| {
                extension
                    .add_op(
                        "rotate".into(),
                        String::new(),
                        expected.clone(),
                        extension_ref,
                    )
                    .unwrap();
            },
        );
        let op = extension.instantiate_extension_op("rotate", [])?;

        for replace_qubit in [false, true] {
            let qubit = if replace_qubit {
                Type::new_tuple([usize_t(), usize_t()])
            } else {
                qb_t()
            };
            let replaceable_types = if replace_qubit {
                let qubit_ty = qb_t().as_extension().unwrap().clone();
                HashSet::from([(qubit_ty.extension().clone(), qubit_ty.name().clone())])
            } else {
                HashSet::new()
            };
            let found = Signature::new(
                [angle.clone(), qubit.clone(), angle.clone(), angle.clone()],
                [
                    qubit.clone(),
                    angle.clone(),
                    angle.clone(),
                    angle.clone(),
                    angle.clone(),
                ],
            );
            // Both rotation inputs are observable, with fan-out of the first, plus an
            // ordinary angle input that must remain directly connected to the body.
            let output_inputs = [1, 0, 0, 2, 3];
            let (replacement, _) = replacement_hugr(found.into(), &output_inputs)?;

            let mut program = ModuleBuilder::new();
            let mut function =
                FunctionBuilder::with_hugr(program.hugr_mut(), "main", expected.clone())?;
            let mut nested =
                function.dfg_builder(expected.body().clone(), function.input_wires())?;
            let args = nested.input_wires().collect_vec();
            let mut outputs = [args[1], args[2], args[2], args[2], args[2]];
            for _ in 0..2 {
                outputs = nested
                    .add_dataflow_op(op.clone(), [args[0], outputs[0], args[2], args[3]])?
                    .outputs_arr();
            }
            let nested = nested.finish_with_outputs(outputs)?;
            function.finish_with_outputs(nested.outputs())?;
            let mut program = program.finish_hugr()?;

            // Exercise the public pass, including inference of the qubit type mapping.
            ImplementOpsPass::new(
                BTreeMap::from([(
                    ("test".to_string(), "rotate".to_string()),
                    (Some(replacement), "impl".to_string()),
                )]),
                replaceable_types,
                HashSet::from([extension.name().clone()]),
                true,
            )
            .run(&mut program)?;

            let calls = program
                .nodes()
                .filter(|node| matches!(program.get_optype(*node), OpType::Call(_)))
                .collect_vec();
            assert_eq!(calls.len(), 2, "replacement should be called directly");
            let implementation = extract_func_node(&program, "impl").unwrap();
            let mut adapted_sig = expected.clone();
            adapted_sig.body_mut().input[1] = qubit.clone();
            adapted_sig.body_mut().output[0] = qubit;
            assert_eq!(
                extract_func_sig(&program, implementation),
                Some(adapted_sig)
            );
            let conversions = program
                .nodes()
                .filter(|node| {
                    program
                        .get_optype(*node)
                        .as_extension_op()
                        .is_some_and(|op| {
                            op.qualified_id().as_str() == "tket.rotation.to_halfturns"
                        })
                })
                .collect_vec();
            assert_eq!(
                conversions.len(),
                2,
                "conversions must be shared by all calls"
            );
            for &conversion in &conversions {
                assert_eq!(program.get_parent(conversion), Some(implementation));
            }
            let [input, output] = program.get_io(implementation).unwrap();
            for (output_index, input_index) in output_inputs.into_iter().enumerate() {
                let origin = program.single_linked_output(output, output_index).unwrap();
                if input_index == 1 || input_index == 2 {
                    assert_eq!(origin, (input, input_index.into()));
                } else {
                    // Trace each adapted output to its own original argument. A graph
                    // with the two rotation inputs swapped would still type-check.
                    let (conversion, _) = program.single_linked_output(origin.0, 0).unwrap();
                    assert!(conversions.contains(&conversion));
                    assert_eq!(
                        program.single_linked_output(conversion, 0),
                        Some((input, input_index.into()))
                    );
                }
            }
            for call in calls {
                let static_port = program.get_optype(call).static_input_port().unwrap();
                let (callee, _) = program.single_linked_output(call, static_port).unwrap();
                assert_eq!(callee, implementation);
            }
        }
        Ok(())
    }

    #[test]
    fn rotation_adapter_rejects_other_signature_mismatches() -> anyhow::Result<()> {
        let angle = Type::new_tuple([float64_type()]);
        let expected: PolyFuncType = Signature::new([rotation_type()], []).into();
        let invalid = [
            (
                "bare float",
                expected.clone(),
                Signature::new([float64_type()], []).into(),
                vec![],
            ),
            (
                "wrong tuple shape",
                expected.clone(),
                Signature::new([Type::new_tuple([float64_type(), float64_type()])], []).into(),
                vec![],
            ),
            (
                "missing input",
                Signature::new([rotation_type(), rotation_type()], []).into(),
                Signature::new([angle.clone()], []).into(),
                vec![],
            ),
            (
                "extra input",
                expected.clone(),
                Signature::new([angle.clone(), angle.clone()], []).into(),
                vec![],
            ),
            (
                "unrelated input type",
                Signature::new([rotation_type(), float64_type()], []).into(),
                Signature::new([angle.clone(), usize_t()], []).into(),
                vec![],
            ),
            (
                "rotation output",
                Signature::new([rotation_type()], [rotation_type()]).into(),
                Signature::new([angle.clone()], [angle.clone()]).into(),
                vec![0],
            ),
            (
                "output-only mismatch",
                Signature::new([angle.clone()], [rotation_type()]).into(),
                Signature::new([angle.clone()], [angle.clone()]).into(),
                vec![0],
            ),
            (
                "polymorphic function",
                PolyFuncType::new([TypeParam::max_nat_kind()], expected.body().clone()),
                PolyFuncType::new(
                    [TypeParam::max_nat_kind()],
                    Signature::new([angle.clone()], []),
                ),
                vec![],
            ),
        ];
        for (case, expected, found, output_inputs) in invalid {
            let (mut replacement, _) = replacement_hugr(found.clone(), &output_inputs)?;
            let before = replacement.store_str(EnvelopeConfig::text())?;
            let mut program = ModuleBuilder::new().finish_hugr()?;
            let replacer = OpReplacer::new_with_types(&mut program, HashMap::new(), true);
            let error = replacer
                .get_func_node(
                    "test.rotate".into(),
                    expected.clone(),
                    &mut replacement,
                    "impl",
                )
                .expect_err(case);
            let OpReplacementError::ExistingFunctionSignatureMismatch {
                expected: error_expected,
                found: error_found,
                ..
            } = error
            else {
                panic!("{case}: wrong error: {error}");
            };
            assert_eq!(*error_expected, expected, "{case}");
            assert_eq!(*error_found, found, "{case}: report the original signature");
            assert_eq!(
                replacement.store_str(EnvelopeConfig::text())?,
                before,
                "{case}"
            );
            replacement.validate()?;
        }
        Ok(())
    }
}
