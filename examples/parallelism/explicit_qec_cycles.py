"""Example of logical programming a GHZ program on log-depth; assuming parallelism,
where transversal CX gates are followed up by error correction.

Since error correction requires applying measurements, if the program is
controlled by a single thread, each one blocks the full program, making the
log-depth GHZ program run in linear time rather than log time.
"""

from guppylang import guppy
from guppylang.emulator import EmulatorBuilder
from guppylang.std.builtins import array
from guppylang.std.platform import output
from selene_sim.backends.bundled_error_models import DepolarizingErrorModel
from selene_sim.backends.bundled_simulators import Stim

from guppyft.code.steane import logical as lg
from guppyft.code.steane.encode import QECPolicy, QECStyle, SteaneBuilder


@guppy
def fully_ft_cx(control: lg.Qubit, target: lg.Qubit) -> None:
    """Apply a fully fault-tolerant CX gate between control and target.

    The transversal CX is followed up by a QEC cycle on both logical qubits,
    ensuring that composing these maintains fault-tolerance.
    """
    lg.cx(control, target)
    lg.qec_cycle(control)
    lg.qec_cycle(target)


@guppy
def log_depth_ghz() -> None:
    # Create some logical qubits
    qs = array(lg.Qubit() for _ in range(8))

    # Layer 0
    lg.h(qs[0])

    # Layer 1
    fully_ft_cx(qs[0], qs[1])

    # Layer 2
    fully_ft_cx(qs[0], qs[2])
    fully_ft_cx(qs[1], qs[3])

    # Layer 3
    fully_ft_cx(qs[0], qs[4])
    fully_ft_cx(qs[1], qs[5])
    fully_ft_cx(qs[2], qs[6])
    fully_ft_cx(qs[3], qs[7])

    # Measure; should be either all 0 or all 1
    ms = array(lg.measure_z(q) for q in qs)
    out = array(m.decode() for m in ms)
    output("all_same", out)


# Produce the physical program and run it
qec_policy = QECPolicy(style=QECStyle.Reichardt)
steane_arch = SteaneBuilder().with_qec_policy(qec_policy).build(n_blocks=8)
encoded_pkg = steane_arch.implement_ops(log_depth_ghz.compile())

out = (
    EmulatorBuilder()
    .build(encoded_pkg, n_qubits=98)
    .with_simulator(Stim())
    .with_error_model(DepolarizingErrorModel(p_1q=1e-5, p_2q=1e-4))
).run()
print(out)
