from typing import no_type_check

from guppylang import guppy
from guppylang.std.angles import angle
from guppylang.std.lang import owned
from guppylang_internals.decorator import custom_function, custom_type, hugr_op

from guppyft.extensions import steane_ops, steane_types
from guppyft.logical._compiler import RotationCompiler, logical_op

OPS_EXTN = steane_ops()
TYPES_EXTN = steane_types()

qubit_type = steane_types.steane_qubit()
measurement_type = steane_types.steane_measurement()


@custom_type(measurement_type, copyable=True, droppable=True)
class Measurement:
    @hugr_op(logical_op("decode", OPS_EXTN))
    @no_type_check
    def decode(self: "Measurement") -> bool:
        """Decode the measurement."""


@custom_type(qubit_type, copyable=False, droppable=False)
class Qubit:
    @hugr_op(logical_op("prep_zero", OPS_EXTN))
    @no_type_check
    def __new__() -> "Qubit": ...

    @guppy
    @no_type_check
    def free(self: "Qubit" @ owned) -> None:
        """Free the qubit."""
        free(self)

    @guppy
    @no_type_check
    def measure_z(self: "Qubit" @ owned) -> Measurement:
        """Destructive measurement of the qubit in the Z basis."""
        return measure_z(self)

    @guppy
    @no_type_check
    def qec_cycle(self: "Qubit") -> None:
        """Perform a QEC cycle on a qubit."""
        qec_cycle(self)

    @guppy
    @no_type_check
    def x(self: "Qubit") -> None:
        """X gate."""
        x(self)

    @guppy
    @no_type_check
    def y(self: "Qubit") -> None:
        """Y gate."""
        y(self)

    @guppy
    @no_type_check
    def z(self: "Qubit") -> None:
        """Z gate."""
        z(self)

    @guppy
    @no_type_check
    def h(self: "Qubit") -> None:
        """H gate."""
        h(self)

    @guppy
    @no_type_check
    def s(self: "Qubit") -> None:
        """S gate."""
        s(self)

    @guppy
    @no_type_check
    def sdg(self: "Qubit") -> None:
        """Sdg gate."""
        sdg(self)

    @guppy
    @no_type_check
    def rz(self: "Qubit", angle: angle) -> None:
        """Rz gate."""
        rz(self, angle)

    @guppy
    @no_type_check
    def inject_magic_for_t(self: "Qubit", magic: "Qubit" @ owned) -> None:
        """Perform a T gate by injecting a magic state."""
        inject_magic_for_t(self, magic)

    @guppy
    @no_type_check
    def inject_magic_for_tdg(self: "Qubit", magic: "Qubit" @ owned) -> None:
        """Perform a Tdg gate by injecting a magic state."""
        inject_magic_for_tdg(self, magic)


@hugr_op(logical_op("free", OPS_EXTN))
@no_type_check
def free(qubit: "Qubit" @ owned) -> None:
    """Free a qubit."""


@hugr_op(logical_op("measure_z", OPS_EXTN))
@no_type_check
def measure_z(qubit: "Qubit" @ owned) -> Measurement:
    """Destructive measurement of the qubit in the Z basis."""


@hugr_op(logical_op("qec_cycle", OPS_EXTN))
@no_type_check
def qec_cycle(qubit: Qubit) -> None:
    """Perform a QEC cycle on a qubit."""


@hugr_op(logical_op("x", OPS_EXTN))
@no_type_check
def x(qubit: Qubit) -> None:
    """X gate."""


@hugr_op(logical_op("y", OPS_EXTN))
@no_type_check
def y(qubit: Qubit) -> None:
    """Y gate."""


@hugr_op(logical_op("z", OPS_EXTN))
@no_type_check
def z(qubit: "Qubit") -> None:
    """Z gate."""


@hugr_op(logical_op("h", OPS_EXTN))
@no_type_check
def h(qubit: "Qubit") -> None:
    """H gate."""


@hugr_op(logical_op("s", OPS_EXTN))
@no_type_check
def s(qubit: "Qubit") -> None:
    """S gate."""


@hugr_op(logical_op("sdg", OPS_EXTN))
@no_type_check
def sdg(qubit: "Qubit") -> None:
    """Sdg gate."""


@custom_function(RotationCompiler("rz", OPS_EXTN))
@no_type_check
def rz(qubit: "Qubit", angle: angle) -> None:
    """Rz gate."""


@hugr_op(logical_op("prep_magic_for_t_like", OPS_EXTN))
@no_type_check
def prep_magic_for_t_like() -> "Qubit":
    """Prepare a magic state that can be used to produce T-like states (T and Tdg)."""


@hugr_op(logical_op("inject_magic_for_t", OPS_EXTN))
@no_type_check
def inject_magic_for_t(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    """Perform a T gate by injecting a magic state."""


@hugr_op(logical_op("inject_magic_for_t", OPS_EXTN))
@no_type_check
def inject_magic_for_tdg(qubit: "Qubit", magic: "Qubit" @ owned) -> None:
    """Perform a Tdg gate by injecting a magic state."""


@hugr_op(logical_op("cx", OPS_EXTN))
@no_type_check
def cx(q0: "Qubit", q1: "Qubit") -> None:
    """CX gate."""


@hugr_op(logical_op("swap", OPS_EXTN))
@no_type_check
def swap(q0: "Qubit", q1: "Qubit") -> None:
    """SWAP gate."""
