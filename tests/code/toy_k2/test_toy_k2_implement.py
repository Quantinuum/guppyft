from guppylang import guppy
from guppylang.std.platform import output

import guppyft.code.toy_k2.logical as k2
from guppyft.code.toy_k2.encode import ToyK2Builder


def test_mix_static_dynq_ops() -> None:

    @guppy
    def main() -> None:
        blk = k2.Block()
        dyn_q = k2.Qubit()

        borrowed_blk, borrowed_q = k2.borrow(blk, 0)
        k2.cx_dynq(dyn_q, borrowed_q)
        blk = k2.restore(borrowed_blk, borrowed_q)
        dyn_q.free()
        k2.measure_z_all(blk)
        output("test", 99)

    pkg = main.with_minimal_opt().compile()

    res = (
        ToyK2Builder()
        .build(n_blocks=2)
        .emulator(pkg, n_qubits=10)
        .run()
        .collated_shots()
    )
    assert res == [{"test": [99]}]
