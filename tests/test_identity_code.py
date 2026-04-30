from guppylang import array, guppy
from guppylang.std.builtins import result
from guppylang.std.option import Option, nothing, some
from hugr.package import Package
from selene_helios_qis_plugin import HeliosInterface, LogLevel
from selene_sim.backends.bundled_simulators import Coinflip
from selene_sim.build import build

from guppyft.globals import map_global_state, with_global_state


@guppy.struct
class Range:
    next: int
    stop: int

    @guppy
    def __iter__(self: "Range") -> "Range":
        return self

    @guppy
    def __next__(self: "Range") -> Option[tuple[int, "Range"]]:
        if self.next >= self.stop:
            return nothing()
        return some((self.next, Range(self.next + 1, self.stop)))

def test_x() -> None:
    @guppy.struct
    class STATE:
        counter: array[int, 1]  # type: ignore[valid-type]

    @guppy(link_name="breakit")
    def break_it(state: STATE) -> None:
        for i in Range(0, 1):
            result("iloop", i)
            if state.counter[0] > 0:
                pass
        result("break_it", 0)

    @guppy(link_name="main")
    def main() -> None:
        map_global_state(break_it)
        result("main", 0)

    @guppy(link_name="wrapper")
    def wrapper() -> None:
        state = STATE(array(0))
        with_global_state(state, main)

    pkg: Package = wrapper.compile()
    with open("my-hugr.hugr", "wb") as f:
        f.write(pkg.to_bytes())
    # pkg.modules[0].render_dot(RenderConfig(display_node_id=True, max_node_label_length=None)).view()

    instance = build(pkg, build_dir="selene-build", interface=HeliosInterface(log_level=LogLevel.DIAGNOSTIC))
    print("Building done!")
    return
    results = list(instance.run(simulator=Coinflip(), n_qubits=0))
    assert results == [('break_it', 0), ('main', 0)]
