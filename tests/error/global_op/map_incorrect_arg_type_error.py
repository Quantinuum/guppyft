from guppylang import guppy

from guppyft.globals import map_global


@guppy
def foo(g: int, i: int) -> int:
    return g

@guppy
def my_prog() -> None:
    map_global(foo, 1.0)

my_prog.compile_function()
