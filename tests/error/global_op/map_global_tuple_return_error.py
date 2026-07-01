from guppylang import guppy

from guppyft.globals import map_global

@guppy
def map_tuple_return(g: tuple[int, int]) -> tuple[int, int]:
    return g

@guppy
def main() -> None:
    map_global(map_tuple_return)

main.compile()
