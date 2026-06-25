from guppylang import guppy, qubit
from guppylang.std.builtins import owned

from guppyft.globals import map_global

@guppy
def foo(qb: qubit @ owned) -> tuple[int, qubit]:
    return 0, qb

@guppy
def my_prog() -> None:
    map_global(foo)

my_prog.compile_function()