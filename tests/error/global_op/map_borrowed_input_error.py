from guppylang import guppy
from guppylang.std.quantum import qubit

from guppyft.globals import map_global

@guppy
def foo(i: int, qb: qubit) -> int:
    return i

@guppy
def main() -> None:
    map_global(foo)

main.compile()
