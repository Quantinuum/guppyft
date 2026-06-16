from guppylang import guppy

from guppyft.globals import with_global


@guppy
def foo() -> None:
    return

@guppy
def main() -> None:
    with_global((1, 1), foo)

main.compile()