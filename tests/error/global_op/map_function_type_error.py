from guppylang import guppy

from guppyft.globals import map_global


@guppy
def my_prog() -> None:
    map_global(1)


my_prog.compile_function()
