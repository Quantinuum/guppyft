"""Builder for public configuration of the Iceberg QEC architecture."""

from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum, auto
from typing import Any, Self

from hugr import Hugr
from hugr.package import Package
from hugr.utils import JsonType

from guppyft._util import PathDict
from guppyft.encode import AnnotatingArchitectureInstance, annotate_encoding

_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RUSStateFactoryConf:
    """Iceberg RUS state factory configuration.

    Attributes:
        size: Maximum number of states to be produced in parallel.
        max_attempts: Maximum number of repeat-until-success attempts.
    """

    size: int
    max_attempts: int

    def to_json(self) -> JsonType:
        """Serialize the RUS state factory config to JSON."""
        return asdict(self)

    @classmethod
    def from_json(
        cls, values: dict[str, Any], *, defaults_from: "RUSStateFactoryConf"
    ) -> "RUSStateFactoryConf":
        """Deserialize the RUS state factory config from JSON."""
        return cls(
            size=values["size"]
            if values.get("size") is not None
            else defaults_from.size,
            max_attempts=values["max_attempts"]
            if values.get("max_attempts") is not None
            else defaults_from.max_attempts,
        )


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


@dataclass
class IcebergQEDPolicy:
    """Policy to determine when QED cycles are injected.

    Each logical block accumulates a cost based on `costs`. Once a block's accumulated
    cost reaches `threshold`, a QED cycle is performed on that block and its counter is
    reset.

    Attributes:
        threshold: Threshold at which a QED cycle is triggered.
        costs: See `IcebergQEDPolicy.OperationCosts`.
    """

    @dataclass
    class OperationCosts:
        """Configuration for operation costs that are used to determined when QED cycles
        should be performed during runtime."""

        idle: float = 0.0
        alloc_dynq: float = 0.0
        x: float = 0.0
        y: float = 0.0
        z: float = 0.0
        x_all: float = 0.0
        y_all: float = 0.0
        z_all: float = 0.0
        x_all_except_at: float = 0.0
        z_all_except_at: float = 0.0
        x_all_except_z_at: float = 0.0
        z_all_except_x_at: float = 0.0
        rx: float = 0.0
        rz: float = 0.0
        pauli_exp_x_all: float = 0.0
        pauli_exp_y_all: float = 0.0
        pauli_exp_z_all: float = 0.0
        pauli_exp_x_all_except_at: float = 0.0
        pauli_exp_z_all_except_at: float = 0.0
        pauli_exp_x_all_except_z_at: float = 0.0
        pauli_exp_z_all_except_x_at: float = 0.0
        h_all: float = 0.0
        cx_all: float = 0.0
        cx_intrablock: float = 0.0
        cx_interblock: float = 0.0
        xx_intrablock: float = 0.0
        yy_intrablock: float = 0.0
        zz_intrablock: float = 0.0
        xx_phase_intrablock: float = 0.0
        xx_phase_interblock: float = 0.0
        yy_phase_intrablock: float = 0.0
        yy_phase_interblock: float = 0.0
        zz_phase_intrablock: float = 0.0
        zz_phase_interblock: float = 0.0
        fan_in: float = 0.0
        fan_out: float = 0.0
        swap_intrablock: float = 0.0

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
        """Serialize the QED policy to JSON."""
        return asdict(self)

    @classmethod
    def from_json(cls, values: dict[str, Any]) -> "IcebergQEDPolicy":
        """Deserialize the QED policy from JSON."""
        costs = IcebergQEDPolicy.OperationCosts(**values.get("costs", {}))
        policy = cls(costs=costs)
        if (threshold := values.get("threshold")) is not None:
            policy.threshold = threshold
        return policy

    @classmethod
    def null_policy(cls) -> "IcebergQEDPolicy":
        """Create a null QED policy where all operations have zero cost
        and no QED is performed."""
        costs = IcebergQEDPolicy.OperationCosts()
        return cls(costs=costs)


@dataclass(frozen=True, kw_only=True)
class _IcebergOptions:
    _n_blocks: int | None
    _block_size: int | None
    qed_policy: IcebergQEDPolicy | None
    syndrome_during_measurement: bool
    state_factory_conf: RUSStateFactoryConf
    dynamic_qubit_reuse: DynamicQubitReuse

    @classmethod
    def _required_value[V](cls, v: V | None, name: str) -> V:
        if v is None:
            raise ValueError(
                f"{name} is not set (should have been validated upon build)!"
            )
        return v

    @property
    def n_blocks(self) -> int:
        return self._required_value(self._n_blocks, "n_blocks")

    @property
    def block_size(self) -> int:
        return self._required_value(self._block_size, "block_size")


@dataclass(frozen=True)
class IcebergInstance(AnnotatingArchitectureInstance):
    """An Iceberg architecture instance built by `IcebergBuilder.build`."""

    _options: _IcebergOptions

    def annotate(self, hugr: Package | Hugr[Any]) -> None:
        """Annotate the current parameters of the Iceberg code architecture on the given
        HUGR's metadata. See `guppyft.encode.annotate_encoding` for more information."""
        assert isinstance(self._options.qed_policy, IcebergQEDPolicy)
        annotate_encoding(
            hugr,
            "iceberg",
            {
                "schema_version": _SCHEMA_VERSION,
                "n_blocks": self._options.n_blocks,
                "block_size": self._options.block_size,
                "qed_policy": self._options.qed_policy.to_json(),
                "syndrome_during_measurement": self._options.syndrome_during_measurement,  # noqa: E501 ruff format keeps changing this line back
                "state_factory": self._options.state_factory_conf.to_json(),
                "dynamic_qubit_reuse": self._options.dynamic_qubit_reuse,
            },
        )


@dataclass(frozen=True, kw_only=True)
class IcebergBuilder:
    """Iceberg architecture builder class for creating `IcebergInstance` objects."""

    _options: _IcebergOptions = field(
        default=_IcebergOptions(
            qed_policy=None,
            _n_blocks=None,
            _block_size=None,
            syndrome_during_measurement=False,
            state_factory_conf=RUSStateFactoryConf(
                size=1,
                max_attempts=3,
            ),
            dynamic_qubit_reuse=DynamicQubitReuse.enabled,
        )
    )

    def with_n_blocks(self, n_blocks: int) -> Self:
        """Set the number of logical blocks the architecture can use."""
        if n_blocks < 0:
            raise ValueError(
                f"Cannot set the number of blocks lower than 0, {n_blocks} given"
            )
        return replace(self, _options=replace(self._options, _n_blocks=n_blocks))

    def with_block_size(self, block_size: int) -> Self:
        """Set the number of logical qubits in a single block."""
        if block_size < 2 or block_size % 2 != 0:
            raise ValueError(
                f"Block size has to be even and at least 2, {block_size} given"
            )
        return replace(self, _options=replace(self._options, _block_size=block_size))

    def with_qed_policy(self, qed_policy: IcebergQEDPolicy) -> Self:
        """Set the QED policy."""
        return replace(self, _options=replace(self._options, qed_policy=qed_policy))

    def with_state_factory_conf(self, conf: RUSStateFactoryConf) -> Self:
        """Set the configuration for the state factory producing Iceberg blocks."""
        if conf.size < 1:
            raise ValueError(
                f"Cannot set the size of the RUS state factory lower than 1,"
                f" {conf.size} given"
            )
        if conf.max_attempts < 1:
            raise ValueError(
                f"Cannot set the max attempts of the RUS state factory lower than 1,"
                f" {conf.max_attempts} given"
            )

        return replace(self, _options=replace(self._options, state_factory_conf=conf))

    def with_syndrome_extraction_during_measurement(self, enabled: bool) -> Self:
        """Set whether syndromes are extracted and checked when measuring a block."""
        return replace(
            self, _options=replace(self._options, syndrome_during_measurement=enabled)
        )

    def with_dynamic_qubit_reuse(self, conf: DynamicQubitReuse) -> Self:
        """Set whether dynamic qubits should be reset and reused."""
        return replace(self, _options=replace(self._options, dynamic_qubit_reuse=conf))

    def _ensure_required_options_set(self) -> None:
        # TODO move validation into options class
        if self._options._n_blocks is None:
            raise ValueError("Option `n_blocks` is required but not set!")
        if self._options._block_size is None:
            raise ValueError("Option `block_size` is required but not set!")

    def build(self) -> IcebergInstance:
        """Build an `IcebergInstance`."""
        self._ensure_required_options_set()
        return IcebergInstance(_options=deepcopy(self._options))

    @classmethod
    def new(cls, *, n_blocks: int, block_size: int) -> Self:
        """Create a new builder with some initial options. Note that the builder
        configuration is not guaranteed to be complete yet."""
        return cls().with_n_blocks(n_blocks).with_block_size(block_size)

    @classmethod
    def instance_from_params(cls, params: dict[str, Any]) -> "IcebergInstance":
        """Produces an instance with the builder according to the given parameters. To
        be used as the 'inverse' of `IcebergInstance.annotate`."""
        return cls.from_params(params).build()

    @classmethod
    def from_params(cls, params: dict[str, Any]) -> Self:
        """Produces a builder according to the given parameters."""
        params = PathDict(params)

        builder = cls.new(n_blocks=params["n_blocks"], block_size=params["block_size"])
        if params["schema_version"] != _SCHEMA_VERSION:
            raise RuntimeError(
                f"Unsupported params schema version: {params['schema_version']}"
            )

        if (qed_policy_params := params.get("qed_policy")) is not None:
            builder = builder.with_qed_policy(
                IcebergQEDPolicy.from_json(qed_policy_params)
            )
        if (state_factory_params := params.get("state_factory")) is not None:
            builder = builder.with_state_factory_conf(
                RUSStateFactoryConf.from_json(
                    state_factory_params,
                    defaults_from=builder._options.state_factory_conf,
                )
            )
        if (
            syndrome_during_measurement := params.get("syndrome_during_measurement")
        ) is not None:
            builder = builder.with_syndrome_extraction_during_measurement(
                syndrome_during_measurement
            )
        if (dynamic_qubit_reuse := params.get("dynamic_qubit_reuse")) is not None:
            builder = builder.with_dynamic_qubit_reuse(dynamic_qubit_reuse)

        return builder
