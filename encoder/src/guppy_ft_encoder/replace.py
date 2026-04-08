from guppylang.defs import GuppyFunctionDefinition
from hugr.package import Package

from ._bindings import RsHugr, _replace_ops


def replace_ops(
    hugr: Package,
    ops: dict[tuple[str, str], GuppyFunctionDefinition],
) -> Package:
    rs_hugr = RsHugr.from_bytes(hugr.modules[0].to_bytes())

    rs_ops = {
        key: RsHugr.from_bytes(val.compile_function().modules[0].to_bytes())
        for key, val in ops.items()
    }

    _replace_ops(rs_hugr, rs_ops)

    return Package.from_bytes(rs_hugr.to_bytes())
