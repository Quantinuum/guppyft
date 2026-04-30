from typing import no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, result

from guppyft.globals import map_global_state, with_global_state
from guppyft.spec import EncoderSpec, OpReplacements


def identity_code_gen() -> EncoderSpec:
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
    @no_type_check
    def _QAlloc() -> tuple[tuple[int, int]]:
        @guppy
        def _impl(state: GLOBAL_STATE) -> tuple[tuple[int, int]]:
            result("_QAlloc", 0)
            state.qec_policy()
            return ((0, 0),)

        return map_global_state(_impl)

    @guppy
    @no_type_check
    def _MeasureFree(_q: tuple[int, int]) -> bool:
        result("_MeasureFree", 0)
        return False

    ops = OpReplacements()
    ops.with_funcs(
        {
            ("tket.quantum", "QAlloc"): _QAlloc,
            ("tket.quantum", "MeasureFree"): _MeasureFree,
        }
    )

    def build_wrapper(func: GuppyFunctionDefinition[[], None]) -> GuppyFunctionDefinition[[], None]:
        @guppy
        @no_type_check
        def wrapper() -> None:
            state = GLOBAL_STATE(array(0))
            with_global_state(state, func)

        return wrapper  # type: ignore[no-any-return]

    return EncoderSpec(ops=ops, build_wrapper=build_wrapper)
