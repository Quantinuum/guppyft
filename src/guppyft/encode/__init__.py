from dataclasses import dataclass

from guppylang.defs import GuppyFunctionDefinition
from hugr.ops import Module
from hugr.package import Package
from hugr.passes.composable import ComposablePass
from tket.passes import NormalizeGuppy

from ._enrichment import EnrichmentSpec, OpReplacements, enrich

__all__ = [
    "EncoderSpec",
    "EnrichmentSpec",
    "OpReplacements",
    "encode",
]


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    """A QEC-code-specific specification for the encoder, usually produced by code
    architectures."""

    lower_to_logical: ComposablePass | None = None
    """Pass to lower from a computational to a logical level, defaults to the
    identity."""
    code_passes: list[ComposablePass] | None = None
    """Passes to run on the logical HUGR, after remaining qubits have been marked as
    dynamically allocated."""
    enrichment: EnrichmentSpec
    """How to enrich / implement logical operations. Passed to the enrichment pass."""


def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncoderSpec,
    *,
    passes: list[ComposablePass] | None = None,
) -> Package:
    """
    Encodes the given package (or Guppy function, directly compiled to a package for
    convenience) by applying computational passes, lowering to a logical level
    (resolving as many qubit allocations statically as possible, marking the rest for
    dynamic allocations) and further lowering the logical operations to the physical
    level, providing their implementations.

    The returned runnable package is guaranteed to be semantically equivalent to the
    given one.

    :param hugr: The package to encode (or Guppy function for convenience).
    :param spec:
    :param passes: Computational passes to run on the given package. Defaults to
        one run of `NormalizeGuppy`.
    :return: The encoded runnable package.
    """

    if isinstance(hugr, GuppyFunctionDefinition):
        hugr = hugr.compile_function()

    assert len(hugr.modules) == 1, "Given package contains more than one module"
    assert not isinstance(hugr.modules[0].entrypoint_op(), Module), (
        "Cannot process module-rooted HUGRs"
    )

    # 1. Run all computational tket passes
    for tket_pass in passes or [NormalizeGuppy()]:
        tket_pass(hugr.modules[0], inplace=True)

    # 2. Static optimisations + static qubit allocations
    if spec.lower_to_logical is not None:
        spec.lower_to_logical(hugr.modules[0], inplace=True)

    # 3. Code specific passes
    for tket_pass in spec.code_passes or []:
        tket_pass(hugr.modules[0], inplace=True)

    # 4. Enrich with global state, QEC policies, etc.
    return enrich(hugr, spec.enrichment)
