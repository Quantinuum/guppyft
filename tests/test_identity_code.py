from guppylang import guppy, array
from guppylang.emulator import EmulatorBuilder
from guppylang.std.builtins import result
from guppylang.std.quantum import measure, qubit
from selene_sim.backends.bundled_simulators import Stim

from guppyft.encoder import _replace_ops
from guppyft.globals import map_global_state, with_global_state
from guppyft.spec import OpReplacements


def test_x() -> None:
    @guppy.struct
    class GLOBAL_STATE:
        qec_counter: array[int, 1]  # type: ignore[valid-type]

        @guppy
        def qec_policy(self: "GLOBAL_STATE") -> None:
            for _ in range(1):
                if self.qec_counter[0] > 0:
                    pass
            result("qec_counter", self.qec_counter)
    @guppy
    def _QAlloc() -> tuple[tuple[int, int]]:
        @guppy
        def _impl(state: GLOBAL_STATE) -> tuple[tuple[int, int]]:
            result("_QAlloc", 0)
            state.qec_policy()
            return ((0, 0),)
        return map_global_state(_impl)

    @guppy
    def _MeasureFree(_q: tuple[int, int]) -> bool:
        result("_MeasureFree", 0)
        return False

    @guppy(link_name="link.main")
    def main() -> None:
        q = qubit()
        result("q", measure(q))

    func_pkg = main.compile()
    func_pkg.modules[0].entrypoint = func_pkg.modules[0].module_root

    ops = OpReplacements()
    ops.with_funcs(
        {
            ("tket.quantum", "QAlloc"): _QAlloc,
            ("tket.quantum", "MeasureFree"): _MeasureFree,
        }
    )
    func_pkg = _replace_ops(func_pkg, ops)

    @guppy.declare(link_name="link.main")
    def func_decl() -> None: ...

    @guppy
    def wrapper() -> None:
        state = GLOBAL_STATE(array(0))
        with_global_state(state, func_decl)

    encoded_pkg = wrapper.compile()
    encoded_pkg = encoded_pkg.link(func_pkg)

    print("Encoding done!")
    runner = EmulatorBuilder().build(encoded_pkg, n_qubits=1).with_simulator(Stim())
    print("Building done!")
    results = runner.run()
    print("Running done!")

    assert results.collated_shots() == [{"_MeasureFree": [0], "_QAlloc": [0], "q": [0]}]