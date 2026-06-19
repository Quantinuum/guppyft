from guppylang import guppy

from guppyft.globals import map_global


@guppy
def foo(i: float) -> int:
    return i  # type: ignore[return-value]

@guppy
def main() -> None:
    map_global(foo)

main.compile()
