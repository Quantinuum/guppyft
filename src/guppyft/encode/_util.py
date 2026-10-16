from typing import Any

from guppylang.defs import GuppyFunctionDefinition
from hugr import Hugr
from hugr.package import Package

from guppyft._bindings import RsHugr


def to_rs_hugr(
    repl: Hugr[Any] | GuppyFunctionDefinition[[Any], Any] | Package,
) -> RsHugr:
    match repl:
        case GuppyFunctionDefinition():
            [module] = repl.compile_function().modules
            return RsHugr.from_bytes(module.to_bytes())
        case Package():
            [module] = repl.modules
            return RsHugr.from_bytes(module.to_bytes())
        case Hugr():
            return RsHugr.from_bytes(repl.to_bytes())
        case _:
            raise TypeError(
                "Expected Hugr or GuppyFunctionDefinition or Package"
                f", got {type(repl)}: {repl}"
            )
