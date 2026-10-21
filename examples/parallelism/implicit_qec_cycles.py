"""Example of logical programming a GHZ program on log-depth; assuming parallelism,
where transversal CX gates are followed up by error correction.

Unlike the `explicit_qec_cycles.py` example, the QEC cycles are introduced
by the runtime policy.
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
def log_depth_ghz() -> None:
    # Create some logical qubits
    qs = array(lg.Qubit() for _ in range(8))

    # Layer 0
    lg.h(qs[0])

    # Layer 1
    lg.cx(qs[0], qs[1])

    # Layer 2
    lg.cx(qs[0], qs[2])
    lg.cx(qs[1], qs[3])

    # Layer 3
    lg.cx(qs[0], qs[4])
    lg.cx(qs[1], qs[5])
    lg.cx(qs[2], qs[6])
    lg.cx(qs[3], qs[7])

    # Measure; should be either all 0 or all 1
    ms = array(lg.measure_z(q) for q in qs)
    out = array(m.decode() for m in ms)
    output("all_same", out)


# We define a QEC policy that will introduce a QEC cycle after each CX gate.
qec_policy = QECPolicy(style=QECStyle.Reichardt, threshold=1)
qec_policy.costs.cx = 1.0

# Produce the physical program and run it
steane_arch = SteaneBuilder().with_qec_policy(qec_policy).build(n_blocks=8)
encoded_pkg = steane_arch.implement_ops(log_depth_ghz.compile())

out = (
    EmulatorBuilder()
    .build(encoded_pkg, n_qubits=98)
    .with_simulator(Stim())
    .with_error_model(DepolarizingErrorModel(p_1q=1e-5, p_2q=1e-4))
).run()
print(out)
