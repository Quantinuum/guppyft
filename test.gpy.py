from guppylang import array, guppy
from guppylang.std.quantum import discard, measure, qubit, x
from guppylang.std.builtins import owned, result
from guppyft.globals import map_global_state, with_global_state

@guppy
def foo(qb: qubit @owned, i: tuple[int, int]) -> tuple[qubit, int]:
    x(qb)
    return qb, i[0] + i[1]

@guppy
def my_prog() -> None:
    i = map_global_state(foo, (9, 10))
    result("my_prog", i)

@guppy
def main() -> None:
    qb = qubit()
    qb = with_global_state(qb, my_prog)
    result("qb_main", measure(qb))

res = main.emulator(n_qubits=1).run().collated_shots()
assert res == [
    {
        "qb_main": [1],
        "my_prog": [19],
    }
]
