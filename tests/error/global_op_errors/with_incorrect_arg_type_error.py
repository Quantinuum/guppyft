from guppylang import guppy

from guppyft.globals import with_global


@guppy
def my_prog(i: int) -> None:
    return


@guppy
def main() -> None:
    with_global(1, my_prog, 1.0)  # type: ignore[call-overload]


main.compile()
