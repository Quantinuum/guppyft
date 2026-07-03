//! The implement pass for replacing operations with function implementations.

#![allow(missing_docs)]

use hugr::{
    Hugr, HugrView, Node,
    builder::{BuildError, HugrBuilder, ModuleBuilder},
    extension::SignatureError,
    hugr::{ValidationError, hugrmut::HugrMut},
    ops::ExtensionOp,
    ops::{DataflowOpTrait, OpType, handle::NodeHandle as _},
    types::{PolyFuncType, Type, TypeRow},
};
use hugr_core::extension::ExtensionId;
use hugr_core::hugr::internal::HugrMutInternals;
use hugr_core::hugr::linking::NodeLinkingError;
use hugr_core::ops::{Call, OpName};
use hugr_core::std_extensions::collections::array::Array;
use hugr_core::std_extensions::collections::borrow_array::BorrowArray;
use hugr_core::types::{SumType, Transformable, TypeArg, TypeName, TypeRowRV};
use hugr_core::{Direction, PortIndex, Visibility};
use itertools::Itertools;
use std::collections::hash_map::Entry;
use std::collections::{BTreeMap, HashMap, HashSet};
use tket::passes::utils::unpack_container::type_unpack::array_args;
use tket::passes::{
    ComposablePass, PassScope, RemoveDeadFuncsError, ReplaceTypes, WithScope,
    replace_types::ReplaceTypesError,
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
    #[display("Type replacement mismatch error. src: {src}, first: {first}, second: {second}.")]
    InconsistentTypeReplacement {
        src: Box<Type>,
        first: Box<Type>,
        second: Box<Type>,
    },
    MissingFunctionHugr {
        name: String,
    },
}

#[derive(Debug, Clone, Default)]
pub struct ImplementOpsPass {
    scope: PassScope,
    pub op_replacements: BTreeMap<(String, String), (Option<Hugr>, String)>,
    ty_replacements: HashSet<(ExtensionId, TypeName)>,
}

impl ImplementOpsPass {
    pub fn new(
        op_replacements: BTreeMap<(String, String), (Option<Hugr>, String)>,
        ty_replacements: HashSet<(ExtensionId, TypeName)>,
    ) -> Self {
        Self {
            op_replacements,
            ty_replacements,
            ..Self::default()
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

        let op_funcs: Vec<(ExtensionOp, Option<Hugr>, &str)> = hugr
            .nodes()
            .filter_map(|n| hugr.get_optype(n).as_extension_op())
            .filter_map(|ext_op| {
                let key = (
                    ext_op.def().extension_id().to_string(),
                    ext_op.def().name().to_string(),
                );
                let (func_hugr, func_name) = self.op_replacements.get(&key)?;
                Some((ext_op.clone(), func_hugr.clone(), func_name.as_str()))
            })
            .unique_by(|(op, _, _)| OpHashWrapper::from(op))
            .collect_vec();

        // Determine type replacements from differences between the `ext_op` and `func_hugr` signatures.
        // Filter using `self.ty_replacements` to only replace specific extension types.
        let type_replacements: Result<Vec<Vec<(Type, Type)>>, ImplementOpsPassError> = op_funcs
            .iter()
            .map(|(op_def, func_hugr, func_name)| {
                let func_hugr =
                    func_hugr
                        .as_ref()
                        .ok_or(ImplementOpsPassError::MissingFunctionHugr {
                            name: func_name.to_string(),
                        })?;
                let src_sig = op_def.signature();
                let tgt_sig = extract_func_sig(func_hugr, func_name)?.instantiate(&[])?;
                // Check that the lengths of the op and func signatures match
                assert_eq!(src_sig.input.len(), tgt_sig.input.len());
                assert_eq!(src_sig.output.len(), tgt_sig.output.len());
                let unpacker = &mut TypeUnpacker::new();
                Ok(src_sig
                    .input
                    .iter()
                    .zip(tgt_sig.input.iter())
                    .chain(src_sig.output.iter().zip(tgt_sig.output.iter()))
                    .filter(|(src, tgt)| src != tgt)
                    .filter_map(|(src, tgt)| {
                        unpacker.unpack_type(src);
                        unpacker
                            .contains_filter_type(self.ty_replacements.clone())
                            .then(|| (src.clone(), tgt.clone()))
                    })
                    .collect_vec())
            })
            .collect();

        let type_replacements_map = type_replacements?.iter().flatten().try_fold(
            HashMap::new(),
            |mut acc: HashMap<Type, Type>, (src, dst)| {
                match acc.entry(src.clone()) {
                    Entry::Vacant(v) => {
                        v.insert(dst.clone());
                        Ok(acc)
                    }
                    Entry::Occupied(o) if o.get() == dst => Ok(acc), // consistent duplicate
                    Entry::Occupied(o) => Err(ImplementOpsPassError::InconsistentTypeReplacement {
                        src: Box::new(o.key().clone()),
                        first: Box::new(o.get().clone()),
                        second: Box::new(dst.clone()),
                    }),
                }
            },
        )?;

        let mut state = ImplementOpsState::new(hugr, &type_replacements_map);
        for (op_def, func_hugr, func_name) in op_funcs {
            state.op(op_def, func_hugr, func_name)?;
        }
        state.finish()?;
        hugr.validate()?;
        Ok(())
    }
}

#[derive(Clone, Default)]
pub struct TypeUnpacker {
    /// Cache of unpacked types.
    cache: HashMap<Type, Vec<Type>>,
}

impl TypeUnpacker {
    pub fn new() -> Self {
        Self {
            cache: HashMap::new(),
        }
    }

    pub fn unpack_type(&mut self, ty: &Type) -> Vec<Type> {
        if self.cache.contains_key(ty) {
            return self.cache.get(ty).cloned().expect("checked above");
        }

        let unpacked = self._new_unpack_type(ty);
        // SAFETY: types form trees so no cycles, cache will not be corrupted
        self.cache.insert(ty.clone(), unpacked.clone());
        unpacked
    }

    fn _new_unpack_type(&mut self, ty: &Type) -> Vec<Type> {
        if let Some(row) = ty.as_sum().and_then(SumType::as_tuple) {
            self.tuple_row(row)
        } else if let Some((size, elem_ty)) = ty
            .as_extension()
            .and_then(|ext| array_args::<Array>(ext).or_else(|| array_args::<BorrowArray>(ext)))
        {
            let inner = self.unpack_type(&elem_ty);
            let total_size = size as usize * inner.len();
            let mut result = Vec::with_capacity(total_size);
            for _ in 0..size {
                result.extend_from_slice(&inner);
            }
            result
        } else {
            vec![ty.clone()]
        }
    }

    fn tuple_row(&mut self, row: &TypeRowRV) -> Vec<Type> {
        TypeRow::try_from(row.clone())
            .expect("unexpected row variable.")
            .iter()
            .flat_map(|t| self.unpack_type(t))
            .collect::<Vec<_>>()
    }

    fn contains_filter_type(&self, filter: HashSet<(ExtensionId, TypeName)>) -> bool {
        self.cache.keys().any(|ty| {
            ty.as_extension()
                .is_some_and(|ct| filter.contains(&(ct.extension().clone(), ct.name().clone())))
        })
    }
}

pub fn extract_func_sig(
    func_hugr: &Hugr,
    func_name: &str,
) -> Result<PolyFuncType, ImplementOpsPassError> {
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

    let func_sig = match &func_hugr.get_optype(func_node) {
        OpType::FuncDecl(decl) => decl.signature(),
        OpType::FuncDefn(defn) => defn.signature(),
        _ => unreachable!(),
    };

    Ok(func_sig.clone())
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
    type_replacer: ReplaceTypes,
    op_calls: HashMap<OpHashWrapper, (OpType, Hugr, Node)>,
}

impl<'a, H: HugrMut<Node = Node>> ImplementOpsState<'a, H> {
    pub fn new(hugr: &'a mut H, types: &'a HashMap<Type, Type>) -> Self {
        for (src, tgt) in types.iter() {
            eprintln!("{} {}", src, tgt)
        }
        let mut type_replacer = ReplaceTypes::default();
        for (src, tgt) in types.iter() {
            type_replacer.set_replace_type(
                src.as_extension()
                    .unwrap_or_else(|| panic!("Failed to unwrap extension for src op: {}.", src))
                    .clone(),
                tgt.clone(),
            );
        }

        Self {
            hugr,
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
        // Replace qubit type
        let op_sig: PolyFuncType = {
            let mut sig = ext_op.signature().into_owned();
            sig.transform(&self.type_replacer)?;
            sig.into()
        };

        // Extract function if given, otherwise generate a declaration with the expected signature.
        let (func_hugr, func_node) = if let Some(hugr) = func_hugr_opt {
            let node = self.extract_func(ext_op.qualified_id(), op_sig, &hugr, func_name)?;
            (hugr, node)
        } else {
            let mut module_builder = ModuleBuilder::new();
            let decl = module_builder.declare(func_name, op_sig)?;
            (module_builder.finish_hugr()?, decl.node())
        };

        // Register call for later replacement
        let call_type: OpType = Call::try_new((*ext_op.signature()).clone().into(), [])?.into();
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

        Ok(())
    }
}
