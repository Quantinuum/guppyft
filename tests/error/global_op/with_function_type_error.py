from guppylang import guppy

from guppyft.globals import with_global


@guppy
def my_prog() -> None:
    with_global(1, 1)


my_prog.compile_function()
