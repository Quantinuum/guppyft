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

def _implement_ops(
        rs_hugr: RsHugr,
        op_replacements: dict[tuple[str, str], tuple[RsHugr | None, str]],
        type_replacements: set[tuple[str, str]]
    ) -> None:
    """
    Replace extension ops in `rs_hugr` to calls to the provided implementations.

    `op_replacements` maps each `(extension_name, op_name)` pair to either a
    compiled implementation HUGR or `None` if only a declaration should be
    generated, together with the function name to use.
    `type_replacements` is a set of extension types that should be replaced by
    the corresponding types in the implementation HUGRs.
    """
