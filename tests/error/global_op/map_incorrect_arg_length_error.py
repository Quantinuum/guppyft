from guppylang import guppy

from guppyft.globals import map_global

@guppy
def foo(i: int, j:int) -> int:
    return i

@guppy
def my_prog() -> None:
    map_global(foo)

my_prog.compile_function()
