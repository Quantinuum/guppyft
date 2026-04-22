#![allow(missing_docs)]

use hugr::{
    Hugr, HugrView, Node,
    builder::{BuildError, Dataflow, DataflowSubContainer, HugrBuilder, ModuleBuilder},
    extension::{
        SignatureError,
        prelude::{bool_t, qb_t},
    },
    hugr::{ValidationError, hugrmut::HugrMut},
    ops::ExtensionOp,
    ops::{DataflowOpTrait, OpType, handle::NodeHandle as _},
    std_extensions::arithmetic::int_types::INT_TYPES,
    types::{PolyFuncType, Signature, Transformable, Type, TypeRV},
};
use hugr_core::builder::Container;
use hugr_core::hugr::internal::HugrMutInternals;
use hugr_core::hugr::linking::NodeLinkingError;
use hugr_core::ops::{Call, OpName, handle::FuncID};
use hugr_core::types::TypeArg;
use hugr_core::{Direction, PortIndex, Visibility};
use itertools::Itertools;
use std::collections::{BTreeMap, HashMap};
use tket::{
    TketOp,
    extension::bool::{BoolOpBuilder, bool_type},
    passes::{
        ComposablePass, PassScope, RemoveDeadFuncsError, ReplaceTypes, WithScope,
        replace_types::ReplaceTypesError,
    },
};

#[derive(derive_more::Error, Debug, derive_more::Display, derive_more::From)]
#[non_exhaustive]
pub enum EncoderPassError {
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
    RemoveDeadFuncsError(RemoveDeadFuncsError),
    #[from]
    NodeLinkingError(NodeLinkingError<Node, Node>),
}

#[derive(Debug, Clone)]
pub struct EncoderPass {
    scope: PassScope,
    qubit_to_ty: Type,
    pub rewrite_ops: BTreeMap<(String, String), Hugr>,
}

impl EncoderPass {
    pub fn new(rewrite_ops: BTreeMap<(String, String), Hugr>) -> Self {
        Self {
            rewrite_ops,
            ..Self::default()
        }
    }
}

impl Default for EncoderPass {
    fn default() -> Self {
        let int: TypeRV = INT_TYPES[6].clone().into();
        Self {
            scope: Default::default(),
            qubit_to_ty: Type::new_tuple(vec![int.clone(), int]),
            rewrite_ops: Default::default(),
        }
    }
}

impl WithScope for EncoderPass {
    fn with_scope(mut self, scope: impl Into<PassScope>) -> Self {
        self.scope = scope.into();
        self
    }
}

impl<H: HugrMut<Node = Node>> ComposablePass<H> for EncoderPass {
    type Error = EncoderPassError;
    type Result = ();

    fn run(&self, hugr: &mut H) -> Result<Self::Result, Self::Error> {
        let op_funcs = self
            .rewrite_ops
            .iter()
            .map(|((ext_name, op_name), func_hugr)| {
                let Some(ext) = hugr.extensions().get(ext_name) else {
                    panic!(
                        "Extension '{ext_name}' not found in HUGR when looking for op '{op_name}' to rewrite! Available extensions: {:?}",
                        hugr.extensions().ids().collect_vec()
                    );
                };

                let op_def = ext.get_op(op_name).unwrap().clone();
                // We cannot handle ops with custom instantiations at the moment
                assert_eq!(op_def.params().unwrap().len(), 0);
                (op_def, func_hugr.clone())
            })
            .collect_vec();

        let mut state = RewriteQuantumState::new(hugr, &self.qubit_to_ty);
        for (op, func_hugr) in op_funcs {
            state.op(ExtensionOp::new(op, [])?, func_hugr)?;
        }
        state.finish()?;
        hugr.validate()?;
        Ok(())
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

struct RewriteQuantumState<'a, H: HugrMut<Node = Node>> {
    hugr: &'a mut H,
    qubit_to_ty: &'a Type,
    type_replacer: ReplaceTypes,
    op_calls: HashMap<OpHashWrapper, (OpType, Hugr, Node)>,
}

impl<'a, H: HugrMut<Node = Node>> RewriteQuantumState<'a, H> {
    pub fn new(hugr: &'a mut H, qubit_to_ty: &'a Type) -> Self {
        let mut type_replacer = ReplaceTypes::default();
        type_replacer.set_replace_type(qb_t().as_extension().unwrap().clone(), qubit_to_ty.clone());

        Self {
            hugr,
            qubit_to_ty,
            type_replacer,
            op_calls: Default::default(),
        }
    }

    pub fn op(&mut self, ext_op: ExtensionOp, mut func_hugr: Hugr) -> Result<(), EncoderPassError> {
        // Replace hugr-bool with tket-bool in function signature
        let expected_func_sig: PolyFuncType = {
            let mut sig = ext_op.signature().into_owned();
            sig.transform(&self.type_replacer)?;
            // bool_t is a sum type, not a CustomType, so ReplaceTypes doesn't handle it.
            // Replace it manually at the top level (original behaviour).
            sig.input
                .iter_mut()
                .chain(sig.output.iter_mut())
                .for_each(|ty| {
                    if ty == &bool_t() {
                        *ty = bool_type();
                    }
                });
            sig.into()
        };

        // Extract target function
        let func_name = ext_op.qualified_id();
        let Some(func_node) = func_hugr.nodes().find(|node| {
            if let Some(name) = match &func_hugr.get_optype(*node) {
                OpType::FuncDecl(decl) => Some(decl.func_name().to_owned()),
                OpType::FuncDefn(defn) => Some(defn.func_name().to_owned()),
                _ => None,
            } {
                name == func_name
            } else {
                false
            }
        }) else {
            panic!(
                "Expected function whose name matches the qualified op name ({}) but it was not found!",
                func_name
            );
        };

        // Test signature
        let func_sig = match &func_hugr.get_optype(func_node) {
            OpType::FuncDecl(decl) => decl.signature(),
            OpType::FuncDefn(defn) => defn.signature(),
            _ => unreachable!(),
        };
        if func_sig != &expected_func_sig {
            return Err(EncoderPassError::ExistingFunctionSignatureMismatch {
                op_id: ext_op.qualified_id(),
                node: func_node,
                name: func_name.to_string(),
                expected: Box::new(expected_func_sig),
                found: Box::new(func_sig.clone()),
            });
        };

        let wrapped_func_hugr = {
            if matches!(ext_op.cast::<TketOp>(), Some(TketOp::Measure)) {
                wrap_measure_declaration(func_hugr, self.qubit_to_ty, &func_name, func_node.into())?
            } else {
                func_hugr.set_entrypoint(func_node);
                func_hugr
            }
        };
        let func_node = wrapped_func_hugr.entrypoint();

        // Register call for later replacement
        let call_type: OpType =
            Call::try_new((*ext_op.signature()).clone().into(), ext_op.args())?.into();
        self.op_calls.insert(
            OpHashWrapper::from(&ext_op),
            (call_type, wrapped_func_hugr, func_node),
        );

        Ok(())
    }

    pub fn finish(mut self) -> Result<(), EncoderPassError> {
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
                    .unwrap();
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

        Ok(())
    }
}

fn wrap_measure_declaration(
    hugr: Hugr,
    qubit_to_ty: &Type,
    func_name: &str,
    func_defn_id: FuncID<true>,
) -> Result<Hugr, BuildError> {
    let mut module_builder = ModuleBuilder::with_hugr(hugr);
    let mut wrapper_func = module_builder.define_function(
        format!("{}.Wrapped", func_name),
        Signature::new([qubit_to_ty.clone()], vec![qubit_to_ty.clone(), bool_t()]),
    )?;
    let [q] = wrapper_func.input_wires_arr();
    let [q, r] = wrapper_func.call(&func_defn_id, &[], [q])?.outputs_arr();
    let [r] = wrapper_func.add_bool_read(r)?;
    let n = wrapper_func.finish_with_outputs([q, r])?.node();
    module_builder.hugr_mut().set_entrypoint(n);
    Ok(module_builder.finish_hugr()?)
}
