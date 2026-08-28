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
        replaceable_types: set[tuple[str, str]]
    ) -> None:
    """
    Replace extension ops in `rs_hugr` to calls to the provided implementations.

    `op_replacements` maps each `(extension_name, op_name)` pair to either a
    compiled implementation HUGR or `None` if only a declaration should be
    generated, together with the function name to use.
    `replaceable_types` is a set of extension types that should be replaced by
    the corresponding types in the implementation HUGRs.
    """

def _replace_encoder(
        rs_hugr: RsHugr,
        op_replacements: dict[tuple[str, str], tuple[str, str, list[int | str]]],
        compound_op_replacements: dict[tuple[str, str], RsHugr],
        ty_replacements: dict[tuple[str, str], tuple[str, str]],
        extensions: str | None = None,
    ) -> None:
    """
    Replace extension ops and types in `rs_hugr` according to the given mappings.

    `op_replacements` maps each source `(extension_name, op_name)` pair (which
    must take no type args) to a target `(extension_name, op_name, args)`
    triple, where `args` is the (possibly empty) list of type args - each
    either an `int` (a `BoundedNat` arg) or a `str` (a `String` arg) - used to
    instantiate the target op.
    `extensions` is an optional JSON-encoded list of additional extension
    definitions to use when resolving the source/target ops and types, for
    extensions not already registered on `rs_hugr`.
    """
