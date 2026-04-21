from guppylang import guppy
from guppylang.std.builtins import result
from guppylang.std.quantum import measure, qubit, x
from hugr.qsystem.result import QsysShot
from selene_sim import Stim, build
from utils.identity_code import identity_code_gen

from guppyft.encoder import auto_encode


def test_x():
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        result("q", measure(q))

    identity_code = identity_code_gen(1)

    prog_bytes = auto_encode(main, identity_code).to_bytes()

    runner = build(prog_bytes)

    assert QsysShot(runner.run(simulator=Stim(), n_qubits=1)).entries[0] == ("q", 1)
