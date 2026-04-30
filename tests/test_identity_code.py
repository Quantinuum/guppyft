from guppylang import array, guppy
from guppylang.std.builtins import result
from selene_sim.backends.bundled_simulators import Coinflip

from guppyft.globals import map_global_state, with_global_state


def test_x() -> None:
    @guppy.struct
    class STATE:
        counter: array[int, 1]  # type: ignore[valid-type]

        @guppy
        def break_it(self: "STATE") -> None:
            for _ in range(1):
                if self.counter[0] > 0:
                    pass
            result("counter", self.counter)

    @guppy
    def main() -> None:
        @guppy
        def _impl(state: STATE) -> None:
            result("_impl", 0)
            state.break_it()

        map_global_state(_impl)
        result("main", 0)

    @guppy
    def wrapper() -> None:
        state = STATE(array(0))
        with_global_state(state, main)

    runner = wrapper.emulator(n_qubits=0).with_simulator(Coinflip())
    print("Building done!")
    results = runner.run()
    assert results[0].as_dict() == {"_impl": 0, "main": 0}
