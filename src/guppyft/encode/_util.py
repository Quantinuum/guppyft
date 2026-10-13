from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr import Hugr
from hugr.envelope import EnvelopeConfig, EnvelopeFormat
from hugr.ops import Call, CallIndirect, LoadFunc
from hugr.package import Package

from guppyft._bindings import RsHugr, _normalize


def to_rs_hugr(
    repl: Hugr[Any] | GuppyFunctionDefinition[[Any], Any] | Package,
) -> RsHugr:
    match repl:
        case GuppyFunctionDefinition():
            [module] = repl.with_minimal_opt().compile_function().modules
            return RsHugr.from_bytes(native_bytes(module))
        case Package():
            [module] = repl.modules
            return RsHugr.from_bytes(native_bytes(module))
        case Hugr():
            return RsHugr.from_bytes(native_bytes(repl))
        case _:
            raise TypeError(
                "Expected Hugr or GuppyFunctionDefinition or Package"
                f", got {type(repl)}: {repl}"
            )


NATIVE_ENVELOPE = EnvelopeConfig(format=EnvelopeFormat.JSON)


def native_bytes(hugr: Hugr[Any]) -> bytes:
    extensions = list(hugr.used_extensions().used_extensions.all_extensions)
    return Package([hugr], extensions).to_bytes(NATIVE_ENVELOPE)


def normalize_application(pkg: Package) -> Package:
    """Normalize without a model round-trip that changes CFG shared outputs."""
    hugr = pkg.modules[0]
    # Guppy with_owned calls a known function indirectly. Make that call static
    # before normalization, so allocating helpers are inlined with the caller.
    for node, data in list(hugr.nodes()):
        if not isinstance(data.op, CallIndirect):
            continue
        (function_wire,) = hugr.linked_ports(node.inp(0))
        load = hugr[function_wire.node].op
        if not isinstance(load, LoadFunc):
            continue
        (target,) = hugr.linked_ports(function_wire.node.inp(0))
        inputs = [(source, port) for source, port in hugr.links() if port.node == node]
        for source, port in inputs:
            hugr.delete_link(source, port)
        data.op = Call(load.signature, load.instantiation, load.type_args)
        for source, port in inputs:
            if port.offset != 0:
                offset = port.offset - 1 if port.offset > 0 else port.offset
                hugr.add_link(source, node.inp(offset))
        hugr.add_link(target, node.inp(len(load.instantiation.input)))
    rs_hugr = RsHugr.from_bytes(native_bytes(hugr))
    _normalize(rs_hugr)
    return Package.from_bytes(rs_hugr.to_bytes(NATIVE_ENVELOPE))
