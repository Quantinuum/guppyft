//! The implement pass for replacing operations with function implementations.

#![allow(missing_docs)]

use hugr::{
    builder::{BuildError, HugrBuilder, ModuleBuilder}, extension::{prelude::qb_t, SignatureError}, hugr::{hugrmut::HugrMut, ValidationError},
    ops::ExtensionOp,
    ops::{handle::NodeHandle as _, DataflowOpTrait, OpType},
    std_extensions::arithmetic::int_types::INT_TYPES,
    types::{PolyFuncType, Type},
    Hugr,
    HugrView,
    Node,
};
use hugr_core::hugr::internal::HugrMutInternals;
use hugr_core::hugr::linking::NodeLinkingError;
use hugr_core::ops::{Call, OpName};
use hugr_core::types::TypeArg;
use hugr_core::{Direction, PortIndex, Visibility};
use itertools::Itertools;
use std::collections::{BTreeMap, HashMap};
use tket::passes::{
    replace_types::ReplaceTypesError, ComposablePass, PassScope, RemoveDeadFuncsError, ReplaceTypes,
    WithScope,
};

#[derive(derive_more::Error, Debug, derive_more::Display, derive_more::From)]
#[non_exhaustive]
pub enum ImplementOpsPassError {
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
pub struct ImplementOpsPass {
    scope: PassScope,
    qubit_to_ty: Type,
    pub op_replacements: BTreeMap<(String, String), (Option<Hugr>, String)>,
}

impl ImplementOpsPass {
    pub fn new(op_replacements: BTreeMap<(String, String), (Option<Hugr>, String)>) -> Self {
        Self {
            op_replacements,
            ..Self::default()
        }
    }
}

impl Default for ImplementOpsPass {
    fn default() -> Self {
        let int: Type = INT_TYPES[6].clone().into();
        Self {
            scope: Default::default(),
            qubit_to_ty: Type::new_tuple(vec![int.clone(), int]),
            op_replacements: Default::default(),
        }
    }
}

impl WithScope for ImplementOpsPass {
    fn with_scope(mut self, scope: impl Into<PassScope>) -> Self {
        self.scope = scope.into();
        self
    }
}

impl<H: HugrMut<Node = Node>> ComposablePass<H> for ImplementOpsPass {
    type Error = ImplementOpsPassError;
    type Result = ();

    fn run(&self, hugr: &mut H) -> Result<Self::Result, Self::Error> {
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

        let op_funcs = self
            .op_replacements
            .iter()
            .filter_map(|((ext_name, op_name), (func_hugr, func_name))| {
                let ext = hugr.extensions().get(ext_name)?;

                let op_def = ext.get_op(op_name).unwrap().clone();
                // We cannot handle ops with custom instantiations at the moment
                assert_eq!(op_def.params().unwrap().len(), 0);
                Some((op_def, func_hugr.clone(), func_name))
            })
            .collect_vec();

        let mut state = ImplementOpsState::new(hugr, &self.qubit_to_ty);
        for (op_def, func_hugr, func_name) in op_funcs {
            state.op(ExtensionOp::new(op_def, [])?, func_hugr, func_name)?;
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

struct ImplementOpsState<'a, H: HugrMut<Node = Node>> {
    hugr: &'a mut H,
    qubit_to_ty: &'a Type,
    type_replacer: ReplaceTypes,
    op_calls: HashMap<OpHashWrapper, (OpType, Hugr, Node)>,
}

impl<'a, H: HugrMut<Node = Node>> ImplementOpsState<'a, H> {
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

    fn extract_func(
        &self,
        op_id: OpName,
        expected_sig: PolyFuncType,
        func_hugr: &Hugr,
        func_name: &str,
    ) -> Result<Node, ImplementOpsPassError> {
        // Extract target function
        let Some(func_node) = func_hugr.children(func_hugr.module_root()).find(|node| {
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
                "Expected hugr containing a function with name '{}' but it was not found!",
                func_name
            );
        };

        // Test signature
        let func_sig = match &func_hugr.get_optype(func_node) {
            OpType::FuncDecl(decl) => decl.signature(),
            OpType::FuncDefn(defn) => defn.signature(),
            _ => unreachable!(),
        };
        if func_sig != &expected_sig {
            return Err(ImplementOpsPassError::ExistingFunctionSignatureMismatch {
                op_id,
                node: func_node,
                name: func_name.to_string(),
                expected: Box::new(expected_sig),
                found: Box::new(func_sig.clone()),
            });
        };

        Ok(func_node)
    }

    pub fn op(
        &mut self,
        ext_op: ExtensionOp,
        func_hugr_opt: Option<Hugr>,
        func_name: &str,
    ) -> Result<(), ImplementOpsPassError> {
        // Replace hugr-bool with tket-bool in function signature
        let op_sig: PolyFuncType = {
            let sig = ext_op.signature().into_owned();
            // sig.transform(&self.type_replacer)?;
            // // bool_t is a sum type, not a CustomType, so ReplaceTypes doesn't handle it.
            // // Replace it manually at the top level (original behaviour).
            // sig.input
            //     .iter_mut()
            //     .chain(sig.output.iter_mut())
            //     .for_each(|ty| {
            //         if ty == &bool_t() {
            //             *ty = bool_type();
            //         }
            //     });
            sig.into()
        };

        // Extract function if given, otherwise generate a declaration with the expected signature.
        let (func_hugr, _) = if let Some(hugr) = func_hugr_opt {
            let node = self.extract_func(ext_op.qualified_id(), op_sig, &hugr, func_name)?;
            (hugr, node)
        } else {
            let mut module_builder = ModuleBuilder::new();
            let decl = module_builder.declare(func_name, op_sig)?;
            (module_builder.finish_hugr()?, decl.node())
        };

        let func_node = func_hugr.entrypoint();

        // Register call for later replacement
        let call_type: OpType =
            Call::try_new((*ext_op.signature()).clone().into(), ext_op.args())?.into();
        self.op_calls.insert(
            OpHashWrapper::from(&ext_op),
            (call_type, func_hugr, func_node),
        );

        Ok(())
    }

    pub fn finish(mut self) -> Result<(), ImplementOpsPassError> {
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
