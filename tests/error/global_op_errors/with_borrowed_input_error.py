from guppylang import guppy
from guppylang.std.quantum import discard, qubit

from guppyft.globals import with_global


@guppy
def my_prog0(qb: qubit) -> None:
    return


@guppy
def main() -> None:
    qb = qubit()
    with_global(1, my_prog0, qb)
    discard(qb)


main.compile()
