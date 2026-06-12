from guppylang import guppy
from guppylang.std.quantum import qubit

from guppyft.globals import map_global


@guppy
def foo(qb: qubit) -> qubit:
    return qb

@guppy
def my_prog() -> None:
    map_global(foo)

my_prog.compile_function()()

