"""Abstractions for constructing QEC architectures."""

import json
from abc import abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder, EmulatorInstance
from hugr import Hugr
from hugr.metadata import Metadata
from hugr.ops import Module
from hugr.package import Package
from hugr.passes.composable import ComposablePass
from tket.passes import Normalize

from ._compile import LogicalCompiler, ReplacementCompiler, UncompilableError
from ._implement_ops import (
    ImplementOps,
    ImplementOpsSpec,
    OpReplacements,
    TyReplacements,
    implement_ops,
)

__all__ = [
    "EncodeSpec",
    "EncoderParams",
    "EncodingArchitecture",
    "ImplementOps",
    "ImplementOpsSpec",
    "LogicalCompiler",
    "OpReplacements",
    "ReplacementCompiler",
    "TyReplacements",
    "UncompilableError",
    "annotate_encoding",
    "encode",
    "implement_ops",
]


class EncodingArchitecture(Protocol):
    def encode(self, pkg: Package) -> Package:
        """Encode a computational package."""
        self._check_may_encode(pkg)
        return self._encode(pkg)

    def implement_ops(self, pkg: Package) -> Package:
        """Implement logical ops in `pkg` using this instance's op implementations."""
        return self._implement_ops(pkg)

    def check_may_encode(self, pkg: Package) -> None:
        """Check whether any issues can be detected that would arise when trying to
        encode the given package, e.g. the package containing unsupported gates.

        Note that this function returning without error is not a guarantee that a
        subsequent call to `encode` will succeed."""
        self._check_may_encode(pkg)

    @abstractmethod
    def _encode(self, pkg: Package) -> Package: ...
    @abstractmethod
    def _check_may_encode(self, pkg: Package) -> None: ...
    @abstractmethod
    def _implement_ops(self, pkg: Package) -> Package: ...

    def emulator(
        self,
        pkg: Package,
        n_qubits: int,
        builder: EmulatorBuilder | None = None,
    ) -> EmulatorInstance:
        """Encode a hugr Package and build an emulator for it.

        Args:
            pkg: The computational hugr package.
            n_qubits: Number of physical qubits available to the emulator.
            builder: Optional `EmulatorBuilder` to use; defaults to a new one.
        """
        encoded_pkg = self.encode(pkg)
        if builder is None:
            builder = EmulatorBuilder()
        return builder.build(encoded_pkg, n_qubits)


@dataclass(frozen=True, kw_only=True)
class EncodeSpec:
    """A QEC-code-specific collection of passes that together fully encode a
    computation."""

    compile: LogicalCompiler | None = None
    """Pass to lower the computation to a logical level."""
    logical_passes: list[ComposablePass] | None = None
    """Additional passes to run on the logical HUGR."""
    implement_ops: ImplementOps | None = None
    """Lowers the logical computation to a physical level."""


def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncodeSpec,
    *,
    passes: list[ComposablePass] | None = None,
) -> Package:
    """
    Encodes the given package (or Guppy function, directly compiled to a package for
    convenience) by applying four stages:

    1. running the given computational passes;
    2. lowering the operations in the package to logical operations and
       potentially performing static optimizations (e.g. resolving some qubit
       address assignments statically);
    3. running additional logical passes (e.g. inserting additional QEC cycles);
       and
    4. implementing the logical operations with physical gates.

    The returned runnable package is guaranteed to be semantically equivalent to the
    given one.

    :param hugr: The package to encode (or Guppy function for convenience).
    :param spec: See ``EncoderSpec``.
    :param passes: Computational passes to run on the given package. Defaults to
        one run of ``Normalize``.
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
    if spec.compile is not None:
        hugr = spec.compile(hugr)

    # 3. Passes with logical -> logical
    for tket_pass in spec.logical_passes or []:
        tket_pass(hugr.modules[0], inplace=True)

    # 4. Lower logical -> physical
    if spec.implement_ops is not None:
        hugr = spec.implement_ops(hugr, as_bytes=False)
    return hugr


class EncoderParams(Protocol):
    def encoding(self) -> str:
        """The encoding to annotate on a program."""

    def params(self) -> Mapping[str, Any]:
        """The parameters to annotate on a program. Implementations should return values
        that support serialization to JSON."""


class _MetadataEncoding(Metadata[Mapping[str, Any]]):
    """Metadata key for annotating parameters with which to encode a program."""

    KEY = "guppyft.encoding"


def annotate_encoding(hugr: Package | Hugr[Any], params: EncoderParams) -> None:
    try:
        json.dumps(params.params(), check_circular=True)
    except TypeError as e:
        raise ValueError("Could not serialize parameters") from e

    for module in hugr.modules if isinstance(hugr, Package) else [hugr]:
        module[module.module_root].metadata[_MetadataEncoding] = {
            "encoding": params.encoding(),
            "params": params.params(),
        }
