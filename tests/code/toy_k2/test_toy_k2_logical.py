from guppylang import guppy
from guppylang.std.builtins import output
from hugr.cli import validate
from tket.passes import InlineFunctions, Normalize

import guppyft.code.toy_k2.logical as k2


def test_guppy_bindings_smoke() -> None:
    """Smoke test: use Guppy to construct a logical HUGR using ops that cover
    all the different signatures from the extension, and check that we can run
    compilation passes on the result."""

    @guppy
    def main() -> None:
        # Ops on blocks
        b0 = k2.Block()
        k2.cx_intra(b0, 1)
        b1 = k2.Block()
        k2.h_all(b1)
        k2.cx_transversal(b0, b1)
        k2.free(b0)
        block_bool0, block_bool1 = k2.measure_z_all(b1).decode()
        output("block_bool0", block_bool0)
        output("block_bool1", block_bool1)
        magic = k2.prep_t_states_non_ft()
        output("magic_bool0", k2.project_z(magic, 0).decode())
        output("magic_bool1", k2.project_z(magic, 1).decode())
        k2.free(magic)

    pkg = main.compile()
    h = pkg.modules[0]
    Normalize()(h, inplace=True)
    InlineFunctions()(h, inplace=True)
    validate(h.to_bytes())


def test_guppy_hugr() -> None:
    """Consistency check of a simple logical HUGR written in Guppy."""

    @guppy
    def main() -> None:
        blk = k2.Block()
        k2.h_all(blk)
        a, b = k2.measure_z_all(blk).decode()
        output("a", a)
        output("b", b)

    pkg = main.compile()
    h = pkg.modules[0]
    InlineFunctions()(h, inplace=True)
    Normalize()(h, inplace=True)
    entrypoint = h.entrypoint
    children = h.children(entrypoint)
    # When https://github.com/Quantinuum/tket2/issues/1691 is implemented, this
    # test will have to change: all the logical ops including `prep_zero_ft`
    # should appear under the entrypoint node. (Possibly we may need to append a
    # final `InlineFunctions()` pass to make that happen.)
    assert {h[child].op.name() for child in children} == {
        "Input",
        "guppyft.toy_k2.ops.prep_zero_ft",
        "guppyft.toy_k2.ops.h_all",
        "guppyft.toy_k2.ops.measure_z_all",
        "Output",
        "guppyft.toy_k2.ops.decode_block_measurement",
        'tket.result.result_bool<"a">',
        'tket.result.result_bool<"b">',
    }
    [h_node] = [child for child in children if "h" in h[child].op.name()]
    assert len(list(h.incoming_links(h_node))) == 1  # CallIndirect
    assert len(list(h.outgoing_links(h_node))) == 1  # free
    validate(h.to_bytes())


def test_non_primitive_logicals_smoke() -> None:
    """Smoke test: use non-primitive logicals functions to construct a logical
    HUGRs, and check that we can run compilation passes on the result.."""

    @guppy
    def main() -> None:
        blk0, blk1 = k2.Block(), k2.Block()

        k2.cx_inter(blk0, 0, blk1, 1)
        k2.h(blk0, 0)
        k2.s_all(blk1)
        k2.s(blk0, 0)
        k2.sdg(blk1, 1)
        k2.t_all(blk0)
        k2.t(blk0, 0)
        k2.tdg(blk1, 1)

        k2.free(blk0)
        k2.free(blk1)

    pkg = main.compile()
    h = pkg.modules[0]
    Normalize()(h, inplace=True)
    InlineFunctions()(h, inplace=True)
    validate(h.to_bytes())
