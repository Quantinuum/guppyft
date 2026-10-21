"""Example of logical programming of multiple teleportation subroutines that are
completely independent from each other and, hence, should be possible to
parallelize if each block had its own thread."""

from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.builtins import array, owned
from guppylang.std.platform import output
from selene_sim.backends.bundled_simulators import Stim

from guppyft.code.steane import logical as lg
from guppyft.code.steane.encode import SteaneBuilder


@guppy
def teleportation(q: lg.Qubit @ owned) -> lg.Qubit:
    """Teleport a logical qubit to a newly created one.

    In order to apply the corrections after teleportation, we need to decode.
    Decoding is a classical operation acting only on the outcomes of the measured
    block. The corrections are also only applied on the block that this
    function returns. Any call to this function on different blocks is
    independent from each other and could, in principle, be parallelized.
    """
    # Create a Bell pair
    q_new = lg.Qubit()
    q_aux = lg.Qubit()
    lg.h(q_aux)
    lg.cx(q_aux, q_new)

    # Perform a Bell measurement to teleport the state
    lg.cx(q, q_aux)
    lg.h(q)
    m1 = q.measure_z()
    m2 = q_aux.measure_z()

    # Decode and apply corrections
    if m2.decode():
        lg.x(q_new)
    if m1.decode():
        lg.z(q_new)

    return q_new


@guppy
def main() -> None:
    # Create some logical qubits
    qs = array(lg.Qubit() for _ in range(4))
    lg.x(qs[0])
    lg.x(qs[2])
    lg.x(qs[3])

    # Teleport each one independently.
    # On the current stack, this will be done sequentially, since each
    # teleportation requires a read on the measurement outcomes.
    teleported_qs = array(teleportation(q) for q in qs)

    # Measure; should result in 1011
    ms = array(lg.measure_z(q) for q in teleported_qs)
    out = array(m.decode() for m in ms)
    output("match1011", out)


# Produce the physical program and run it
steane_arch = SteaneBuilder().build(n_blocks=12)  # 4+8 to account for Bell states
encoded_pkg = steane_arch.implement_ops(main.compile())

out = (EmulatorBuilder().build(encoded_pkg, n_qubits=98).with_simulator(Stim())).run()
print(out)
