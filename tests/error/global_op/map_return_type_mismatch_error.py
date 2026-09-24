from guppylang import guppy
from guppylang.std.builtins import owned
from guppylang.std.quantum import qubit

from guppyft.globals import map_global


@guppy
def map_func(q: qubit @ owned) -> tuple[qubit, tuple[int, int]]:
    return q, (0, 0)


@guppy
def foo() -> tuple[int, int]:
    return map_global(map_func)


foo.compile_function()
