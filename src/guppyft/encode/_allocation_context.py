"""Pass an allocation capability only through functions which allocate blocks.

Gate implementations obtain shared state from their logical block values. Only
allocation, which has no input block, needs this extra borrowed argument.
"""

from graphlib import TopologicalSorter

from hugr import Hugr, ops, tys


def add_allocation_context(
    hugr: Hugr, names: set[str], context: tys.Type, root_name: str
) -> None:
    functions = {
        n
        for n, d in hugr.nodes()
        if isinstance(d.op, (ops.FuncDefn, ops.FuncDecl)) and d.op.f_name in names
    }
    calls = {}
    for n, d in hugr.nodes():
        if isinstance(d.op, ops.Call):
            (target,) = hugr.linked_ports(n.inp(len(d.op.instantiation.input)))
            calls[n] = target.node

    def ancestors(n):
        while (n := hugr[n].parent) is not None:
            yield n

    def enclosing_function(n):
        return next(a for a in ancestors(n) if isinstance(hugr[a].op, ops.FuncDefn))

    roots = {
        n
        for n, d in hugr.nodes()
        if isinstance(d.op, ops.FuncDefn) and d.op.f_name == root_name
    }
    reachable = set(roots)
    while True:
        added = {
            target for n, target in calls.items() if enclosing_function(n) in reachable
        } - reachable
        if not added:
            break
        reachable |= added
    calls = {
        n: target for n, target in calls.items() if enclosing_function(n) in reachable
    }
    functions = (functions & reachable) | roots

    # Include callers transitively, but leave gate-only functions unchanged.
    while True:
        affected = {n for n, target in calls.items() if target in functions}
        callers = {
            a
            for n in affected
            for a in ancestors(n)
            if isinstance(hugr[a].op, ops.FuncDefn)
        }
        added = callers - functions
        if not added:
            break
        functions |= added
    for n, d in hugr.nodes():
        if (
            isinstance(d.op, ops.LoadFunc)
            and list(hugr.linked_ports(n.out(0)))
            and enclosing_function(n) in reachable
            and any(p.node in functions for p in hugr.linked_ports(n.inp(0)))
        ):
            raise ValueError(
                "Allocation through higher-order functions is not supported"
            )
    containers = {a for n in affected for a in ancestors(n) if a not in functions}
    containers.discard(hugr.module_root)
    supported = (
        ops.DFG,
        ops.Conditional,
        ops.Case,
        ops.TailLoop,
        ops.CFG,
        ops.DataflowBlock,
    )
    if any(not isinstance(hugr[n].op, supported) for n in containers):
        raise ValueError("Unsupported allocation control-flow container")
    # Every case must pass the capability, including cases which do not allocate.
    for n in list(containers):
        if isinstance(hugr[n].op, (ops.Conditional, ops.CFG)):
            containers.update(hugr.children(n))

    def extend(sig):
        return tys.FunctionType([*sig.input, context], [*sig.output, context])

    for n in functions:
        op = hugr[n].op
        if isinstance(op, ops.FuncDecl):
            op.signature = tys.PolyFuncType(
                op.signature.params, extend(op.signature.body)
            )
        else:
            op.inputs = [*op.inputs, context]
            op._outputs = [*op.outputs, context]
    for n in affected:
        op = hugr[n].op
        old_static = n.inp(len(op.instantiation.input))
        (source,) = hugr.linked_ports(old_static)
        hugr.delete_link(source, old_static)
        op.signature = tys.PolyFuncType(op.signature.params, extend(op.signature.body))
        op.instantiation = extend(op.instantiation)
        hugr._update_port_count(
            n,
            num_inps=len(op.instantiation.input) + 1,
            num_outs=len(op.instantiation.output),
        )
        hugr.add_link(source, n.inp(len(op.instantiation.input)))
    for n in containers:
        op = hugr[n].op
        if isinstance(op, ops.ExitBlock):
            op._cfg_outputs = [*op.cfg_outputs, context]
            continue
        if isinstance(op, ops.DataflowBlock):
            op.inputs = [*op.inputs, context]
            op._other_outputs = [*op.other_outputs, context]
            continue
        if isinstance(op, ops.Conditional):
            op.other_inputs = [*op.other_inputs, context]
            op._outputs = [*op.outputs, context]
        elif isinstance(op, ops.TailLoop):
            op.rest = [*op.rest, context]
        else:
            op.inputs = [*op.inputs, context]
            op._outputs = [*op.outputs, context]
        if not isinstance(op, ops.Case):
            sig = op.outer_signature()
            hugr._update_port_count(
                n, num_inps=len(sig.input), num_outs=len(sig.output)
            )

    # Wire one capability through each dataflow region, respecting existing value
    # and order dependencies. No capability is copied or discarded by the pass.
    for parent in functions | containers:
        if isinstance(
            hugr[parent].op, (ops.FuncDecl, ops.Conditional, ops.CFG, ops.ExitBlock)
        ):
            continue
        children = set(hugr.children(parent))
        (inp,) = [n for n in children if isinstance(hugr[n].op, ops.Input)]
        (out,) = [n for n in children if isinstance(hugr[n].op, ops.Output)]
        in_op, out_op = hugr[inp].op, hugr[out].op
        in_op.types = [*in_op.types, context]
        out_op._types = [*out_op._types, context]
        hugr._update_port_count(inp, num_outs=len(in_op.types))
        hugr._update_port_count(out, num_inps=len(out_op._types), num_outs=0)
        dependencies = {n: set() for n in children}
        for source, target in hugr.links():
            if source.node in children and target.node in children:
                dependencies[target.node].add(source.node)
        wire = inp.out(len(in_op.types) - 1)
        for n in TopologicalSorter(dependencies).static_order():
            if n not in affected and n not in containers:
                continue
            op = hugr[n].op
            sig = op.outer_signature()
            hugr.add_link(wire, n.inp(len(sig.input) - 1))
            wire = n.out(len(sig.output) - 1)
        hugr.add_link(wire, out.inp(len(out_op._types) - 1))
