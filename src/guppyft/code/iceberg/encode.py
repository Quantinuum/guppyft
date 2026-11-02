"""Builder for public configuration of the Iceberg QEC architecture."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Self

from guppyft.encode import annotate_encoding

if TYPE_CHECKING:
    from hugr import Hugr
    from hugr.package import Package
    from hugr.utils import JsonType


class DynamicQubitReuse(StrEnum):
    """Configuration for how dynamic qubits are allocated or reused. Fresh qubits are
    from block allocations and have not yet been allocated. When dynamic qubits are
    freed, depending on the configuration, future dynamic qubit allocations can reset
    and reuse these qubits.

    When all dynamic qubits from a logical block have been freed, the block itself is
    freed and becomes available to be reallocated."""

    disabled = auto()
    """Only allocate fresh qubits from logical block allocations. Do not reset and reuse
    dynamic qubits."""
    if_necessary = auto()
    """Prefer using fresh logical qubits. Only reuse logical qubits if no more blocks
    are available to be allocated."""
    enabled = auto()
    """Use available fresh qubits, then freed qubits, before preparing another block."""


class InitStyle(StrEnum):
    """The initialisation style of an Iceberg block."""

    HALF_DEPTH = auto()
    LOG_DEPTH = auto()


@dataclass
class IcebergQEDPolicy:
    """Policy to determine when QED cycles are injected.

    Each logical block accumulates a cost based on `costs`. Once a block's accumulated
    cost reaches `threshold`, a QED cycle is performed on that block and its counter is
    reset.

    Attributes:
        threshold: Threshold at which a QED cycle is triggered.
        costs: See `OperationCosts`.
    """

    @dataclass
    class OperationCosts:
        """Configuration for operation costs that are used to determined when QED cycles
        should be performed during runtime."""

        idle: float = 0.0
        all_x: float = 0.0
        all_y: float = 0.0
        all_z: float = 0.0
        all_but_one_x: float = 0.0
        all_but_one_z: float = 0.0
        all_h: float = 0.0
        x_with_all_but_one_z: float = 0.0
        z_with_all_but_one_x: float = 0.0
        cx_transversal: float = 0.0
        yy_phase_intrablock: float = 0.0
        xx_phase_interblock: float = 0.0
        yy_phase_interblock: float = 0.0
        alloc_dynq: float = 0.0
        x: float = 0.0
        y: float = 0.0
        z: float = 0.0
        xx: float = 0.0
        yy: float = 0.0
        zz: float = 0.0
        cx_intrablock: float = 0.0
        cx_interblock: float = 0.0
        fan_in: float = 0.0
        fan_out: float = 0.0
        swap: float = 0.0
        rx: float = 0.0
        ry: float = 0.0
        rz: float = 0.0
        all_rx: float = 0.0
        all_ry: float = 0.0
        all_rz: float = 0.0
        all_but_one_rx: float = 0.0
        all_but_one_rz: float = 0.0
        xx_phase_intrablock: float = 0.0
        zz_phase_intrablock: float = 0.0
        zz_phase_interblock: float = 0.0

        def __setattr__(self, key: str, value: Any) -> None:
            """Set a non-negative cost for a known logical operation."""
            if not hasattr(self, key):
                raise KeyError(f"Unknown cost key: {key}")
            if value < 0:
                raise ValueError(f"Op cost cannot be negative: received {value}")
            super().__setattr__(key, value)

    threshold: int = 1
    costs: OperationCosts = field(default_factory=OperationCosts)

    def to_json(self) -> JsonType:
        """Serialise the QED policy to JSON."""
        return asdict(self)


@dataclass(frozen=True, kw_only=True)
class _IcebergOptions:
    init_style: InitStyle
    qed_policy: IcebergQEDPolicy
    syndrome_during_measurement: bool
    state_prep_rus_attempts: int
    dynamic_qubit_reuse: DynamicQubitReuse


@dataclass(frozen=True)
class IcebergInstance:
    """An Iceberg architecture instance built by `IcebergBuilder.build`."""

    _n_blocks: int
    _block_size: int
    _options: _IcebergOptions

    def annotate(self, hugr: Package | Hugr[Any]) -> None:
        """Annotate the current parameters of the Iceberg code architecture on the given
        HUGR's metadata. See `guppyft.encode.annotate_encoding` for more information."""
        annotate_encoding(
            hugr,
            "iceberg",
            {
                "schema_version": 1,
                "n_blocks": self._n_blocks,
                "block_size": self._block_size,
                "init_style": self._options.init_style,
                "qed_policy": self._options.qed_policy.to_json(),
                "syndrome_during_measurement": self._options.syndrome_during_measurement,  # noqa: E501 ruff format keeps changing this line back
                "state_prep_rus_attempts": self._options.state_prep_rus_attempts,
                "dynamic_qubit_reuse": self._options.dynamic_qubit_reuse,
            },
        )


@dataclass(frozen=True, kw_only=True)
class IcebergBuilder:
    """Iceberg architecture builder class for creating `IcebergInstance` objects."""

    _options: _IcebergOptions = field(
        default=_IcebergOptions(
            init_style=InitStyle.LOG_DEPTH,
            qed_policy=IcebergQEDPolicy(),
            syndrome_during_measurement=False,
            state_prep_rus_attempts=3,
            dynamic_qubit_reuse=DynamicQubitReuse.enabled,
        )
    )

    def with_qed_policy(self, qed_policy: IcebergQEDPolicy) -> Self:
        """Set the QED policy."""
        return replace(self, _options=replace(self._options, qed_policy=qed_policy))

    def with_init_style(self, style: InitStyle) -> Self:
        """Set the state initialization style."""
        return replace(self, _options=replace(self._options, init_style=style))

    def with_state_prep_rus_attempts(self, max_attempts: int) -> Self:
        """Set the number of attempts state prep is allowed before it fails."""
        return replace(
            self, _options=replace(self._options, state_prep_rus_attempts=max_attempts)
        )

    def with_syndrome_extraction_during_measurement(self, enabled: bool) -> Self:
        """Set whether syndromes are extracted and checked when measuring a block."""
        return replace(
            self, _options=replace(self._options, syndrome_during_measurement=enabled)
        )

    def with_dynamic_qubit_reuse(self, conf: DynamicQubitReuse) -> Self:
        """Set whether dynamic qubits should be reset and reused."""
        return replace(self, _options=replace(self._options, dynamic_qubit_reuse=conf))

    def build(self, *, n_blocks: int, block_size: int) -> IcebergInstance:
        """Build an `IcebergInstance` configured for `n_blocks` logical blocks each
        with `block_size` logical qubits."""
        return IcebergInstance(
            _n_blocks=n_blocks, _block_size=block_size, _options=deepcopy(self._options)
        )
