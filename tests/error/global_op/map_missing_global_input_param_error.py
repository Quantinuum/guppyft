from guppylang import guppy

from guppyft.globals import map_global


@guppy
def foo() -> int:
    return 0

@guppy
def my_prog() -> None:
    map_global(foo)

my_prog.compile()