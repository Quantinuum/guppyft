"""Typing stubs for the bindings defined in the `rust-bindings` crate."""

from hugr.envelope import EnvelopeConfig

class RsHugr:
    """Rust-backed Hugr."""
    def to_bytes(self, config: EnvelopeConfig | None = None) -> bytes:
        """Encode the Hugr as a bytes object."""

    def to_str(self, config: EnvelopeConfig | None = None) -> str:
        """Encode the Hugr as a string."""

    @classmethod
    def from_bytes(cls, bytes: bytes, config: EnvelopeConfig | None = None) -> RsHugr:
        """Decode the Hugr from a bytes object."""

    @classmethod
    def from_str(cls, str: str, config: EnvelopeConfig | None = None) -> RsHugr:
        """Decode the Hugr from a string."""

    def mermaid_string(self) -> str:
        """Render the Hugr as a Mermaid string."""

def _replace_ops(rs_hugr: RsHugr, ops: dict[tuple[str, str], RsHugr]) -> None:
    """
    TODO
    """
