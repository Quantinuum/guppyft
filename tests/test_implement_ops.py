from dataclasses import replace
from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.angles import angle
from guppylang.std.builtins import array
from guppylang.std.debug import state_output
from guppylang.std.platform import output
from guppylang.std.quantum import h, qubit, rz

from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)


@pytest.mark.parametrize("as_bytes", [False, True])
def test_default_build_wrapper(as_bytes: bool) -> None:
    @guppy
    def main() -> None:
        pass

    pkg0 = main.compile()
    [module] = pkg0.modules
    entrypoint = module.entrypoint
    before = pkg0.to_str()
    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())

    pkg1 = (
        implement_ops(pkg0, spec, as_bytes=True)
        if as_bytes
        else implement_ops(pkg0, spec)
    )

    assert pkg0.to_str() == before
    [module_after] = pkg0.modules
    assert module_after is module
    assert module.entrypoint == entrypoint

    EmulatorBuilder().build(pkg1, n_qubits=1).run()


@pytest.mark.parametrize(
    "adapt_rotation_inputs", [False, True], ids=["disabled", "enabled"]
)
def test_rotation_input_adaptation(adapt_rotation_inputs: bool) -> None:
    @guppy
    def replacement(q: qubit, phase: angle) -> None:
        output("phase", phase.halfturns)
        rz(q, phase)

    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        h(q)
        for phase in array(0.0, 0.13, -0.31, 7.1):
            rz(q, angle(phase))
            state_output("q", q)
        q.discard()

    spec = ImplementOpsSpec(
        ops=OpReplacements().with_func(("tket.quantum", "Rz"), replacement),
        tys=TyReplacements(),
    )
    if adapt_rotation_inputs is not None:
        spec = replace(spec, adapt_rotation_inputs=adapt_rotation_inputs)
    pkg = main.with_minimal_opt().compile()
    before = pkg.to_str()
    if not adapt_rotation_inputs:
        with pytest.raises(RuntimeError, match="does not have the expected signature"):
            implement_ops(pkg, spec)
        assert pkg.to_str() == before
        return
    result = implement_ops(pkg, spec)
    assert pkg.to_str() == before
    [original_states] = EmulatorBuilder().build(pkg, n_qubits=1).run().partial_states()
    replaced_result = EmulatorBuilder().build(result, n_qubits=1).run()
    [shot] = replaced_result.collated_shots()
    assert shot["phase"] == [0.0, 0.13, -0.31, 7.1]
    [replaced_states] = replaced_result.partial_states()

    assert [tag for tag, _ in original_states] == ["q"] * 4
    assert [tag for tag, _ in replaced_states] == ["q"] * 4
    for (_, original), (_, replaced) in zip(
        original_states, replaced_states, strict=True
    ):
        assert replaced.as_single_state() == pytest.approx(
            original.as_single_state(), rel=1e-12, abs=1e-12
        )
