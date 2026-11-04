from dataclasses import asdict, dataclass

from hugr.utils import JsonType


@dataclass(frozen=True)
class RUSStateFactoryConf:
    """RUS state factory configuration.

    Attributes:
        size: Maximum number of states to be produced in parallel.
        max_attempts: Maximum number of repeat-until-success attempts.
    """

    size: int
    max_attempts: int

    def to_json(self) -> JsonType:
        """Serialise the RUS state factory config to JSON."""
        return asdict(self)
