import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from guppylang.defs import GuppyFunctionDefinition
from hugr import Hugr
from hugr.metadata import Metadata
from hugr.ops import Module
from hugr.package import Package
from hugr.passes.composable import ComposablePass
from tket.passes import Normalize

from ._implement_ops import (
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)
from ._to_logical import ReplacementCompiler

__all__ = [
    "EncoderParams",
    "EncoderSpec",
    "ImplementOpsSpec",
    "OpReplacements",
    "ReplacementCompiler",
    "TyReplacements",
    "annotate_encoding",
    "encode",
    "implement_ops",
]


@dataclass(frozen=True, kw_only=True)
class EncoderSpec:
    """A QEC-code-specific specification for the encoder, usually produced by code
    architectures."""

    to_logical: ComposablePass | None = None
    """Pass to lower the computation to a logical level, defaults to the identity
    without static qubit allocation."""
    logical_passes: list[ComposablePass] | None = None
    """Additional passes to run on the logical HUGR."""
    implement_spec: ImplementOpsSpec
    """How to implement logical operations. Passed to the implement ops pass."""


def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncoderSpec,
    *,
    passes: list[ComposablePass] | None = None,
) -> Package:
    """
    Encodes the given package (or Guppy function, directly compiled to a package for
    convenience) by applying four stages: 1. Run the given computational passes,
    2. lower the operations in the package to logical operations and potentially perform
    static optimisations (e.g. resolving some qubit address assignments statically),
    3. running additional logical passes (e.g. inserting additional QEC cycles), and
    4. implementing the logical operations with physical gates.

    The returned runnable package is guaranteed to be semantically equivalent to the
    given one.

    :param hugr: The package to encode (or Guppy function for convenience).
    :param spec: See `EncoderSpec`.
    :param passes: Computational passes to run on the given package. Defaults to
        one run of `Normalize`.
    :return: The encoded runnable package.
    """

    if isinstance(hugr, GuppyFunctionDefinition):
        hugr = hugr.compile_function()

    assert len(hugr.modules) == 1, "Given package contains more than one module"
    assert not isinstance(hugr.modules[0].entrypoint_op(), Module), (
        "Cannot process module-rooted HUGRs"
    )

    # 1. Passes with computational -> computational
    for tket_pass in passes or [Normalize()]:
        tket_pass(hugr.modules[0], inplace=True)

    # 2. Lower computational -> logical
    if spec.to_logical is not None:
        spec.to_logical(hugr.modules[0], inplace=True)

    # 3. Passes with logical -> logical
    for tket_pass in spec.logical_passes or []:
        tket_pass(hugr.modules[0], inplace=True)

    # 4. Lower logical -> physical
    return implement_ops(hugr, spec.implement_spec)


class EncoderParams(Protocol):
    def encoding(self) -> str:
        """The encoding to annotate on a program."""

    def params(self) -> Mapping[str, Any]:
        """The parameters to annotate on a program. Implementations should return values
        that support serialisation to JSON."""


class _MetadataEncoding(Metadata[Mapping[str, Any]]):
    """Metadata key for annotating parameters with which to encode a program."""

    KEY = "guppyft.encoding"


def annotate_encoding(hugr: Package | Hugr[Any], params: EncoderParams) -> None:
    try:
        json.dumps(params.params(), check_circular=True)
    except TypeError as e:
        raise ValueError("Could not serialise parameters") from e

    for module in hugr.modules if isinstance(hugr, Package) else [hugr]:
        module[module.module_root].metadata[_MetadataEncoding] = {
            "encoding": params.encoding(),
            "params": params.params(),
        }
