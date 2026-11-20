from typing import TYPE_CHECKING, no_type_check

import pytest
from guppylang import guppy, qubit
from guppylang.emulator import EmulatorBuilder
from guppylang.library import GuppyLibrary, link_name
from guppylang.std.angles import angle
from guppylang.std.builtins import array
from guppylang.std.debug import state_output
from guppylang.std.platform import output
from guppylang.std.quantum import discard, h, rz, x, z
from hugr.ops import ExtOp

from guppyft.encode import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)

if TYPE_CHECKING:
    from hugr.package import Package


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
        adapt_rotation_inputs=adapt_rotation_inputs,
    )
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


def test_preserves_packaged_extensions_for_opaque_ops() -> None:
    """Regression test for implementing ops on a hugr with opaque ops where the
    extensions are packaged but not resolved."""

    @guppy
    def main() -> None:
        discard(qubit())

    pkg1: Package = main.compile()

    [hugr] = pkg1.modules
    for node_data in hugr.values():
        if isinstance(node_data.op, ExtOp):
            node_data.op = node_data.op.to_custom_op()  # Make all ops opaque

    spec = ImplementOpsSpec(ops=OpReplacements(), tys=TyReplacements())
    pkg2 = implement_ops(pkg1, spec)

    assert {e.name for e in pkg1.extensions}.issubset({e.name for e in pkg2.extensions})


@pytest.mark.parametrize("from_headers", [False, True])
def test_missing_op_explicit_generation(from_headers: bool) -> None:
    header_lib = GuppyLibrary()
    lib = GuppyLibrary()
    ops = OpReplacements()

    @header_lib.register_member
    @guppy.declare
    @link_name("test.guppyft.replacement")
    @no_type_check
    def replacement_decl(q: qubit) -> None: ...
    @lib.register_member
    @guppy
    @link_name("test.guppyft.replacement")
    @no_type_check
    def replacement(q: qubit) -> None:
        x(q)

    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        z(q)  # Intentionally replace Z with X to observe an encoding change
        output("res", q.measure().read())

    ops.with_generated_decl(("tket.quantum", "Z"), "test.guppyft.replacement")
    compiled_lib = lib.compile()
    if from_headers:
        ops.gen_missing_decls_from_lib(header_lib.compile())
    else:
        ops.gen_missing_decls_from_lib(compiled_lib)

    spec = ImplementOpsSpec(ops=ops, tys=TyReplacements(), libs=[compiled_lib])
    pkg1 = main.with_minimal_opt().compile()
    pkg2 = implement_ops(pkg1, spec)

    [shot] = list(EmulatorBuilder().build(pkg2, n_qubits=1).run())
    assert shot.as_dict() == {"res": 1}


def test_missing_op_declaration_error() -> None:
    lib = GuppyLibrary()
    ops = OpReplacements()

    @lib.register_member
    @guppy
    @link_name("test.guppyft.replacement")
    @no_type_check
    def replacement(q: qubit) -> None:
        x(q)

    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        z(q)
        output("res", q.measure().read())

    ops.with_generated_decl(("tket.quantum", "Z"), "test.guppyft.replacement")
    # Forget to generate missing declarations from the library

    spec = ImplementOpsSpec(ops=ops, tys=TyReplacements(), libs=[lib.compile()])
    pkg1 = main.with_minimal_opt().compile()

    with pytest.raises(
        ValueError,
        match=r"Op replacement spec is unfinished: Function declarations are missing: test.guppyft.replacement \(for tket.quantum.Z\)",  # noqa: E501
    ):
        implement_ops(pkg1, spec)


@pytest.mark.parametrize("from_headers", [False, True])
def test_library_as_bytes(from_headers: bool) -> None:
    header_lib = GuppyLibrary()
    lib = GuppyLibrary()
    ops = OpReplacements()

    @header_lib.register_member
    @guppy.declare
    @link_name("test.guppyft.replacement")
    @no_type_check
    def replacement_decl(q: qubit) -> None: ...
    @lib.register_member
    @guppy
    @link_name("test.guppyft.replacement")
    @no_type_check
    def replacement(q: qubit) -> None:
        x(q)

    @guppy
    @no_type_check
    def main() -> None:
        q = qubit()
        z(q)  # Intentionally replace Z with X to observe an encoding change
        output("res", q.measure().read())

    ops.with_generated_decl(("tket.quantum", "Z"), "test.guppyft.replacement")
    compiled_lib = lib.compile()
    if from_headers:
        ops.gen_missing_decls_from_lib(header_lib.compile())
    else:
        ops.gen_missing_decls_from_lib(compiled_lib)
    lib_bytes = compiled_lib.to_bytes()

    spec = ImplementOpsSpec(ops=ops, tys=TyReplacements(), libs=[lib_bytes])
    pkg1 = main.with_minimal_opt().compile()
    pkg2 = implement_ops(pkg1, spec)

    [shot] = list(EmulatorBuilder().build(pkg2, n_qubits=1).run())
    assert shot.as_dict() == {"res": 1}
