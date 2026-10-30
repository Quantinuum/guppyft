"""Abstractions for constructing QEC architectures."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, overload

from guppylang.defs import GuppyFunctionDefinition
from guppylang.emulator import EmulatorBuilder, EmulatorInstance
from hugr import Hugr
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
    "AnnotatingArchitectureInstance",
    "EncodeSpec",
    "EncodingArchitectureInstance",
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


class AnnotatingArchitectureInstance(Protocol):
    """An architecture instance capable of annotating a package for delayed / remote
    encoding. See `guppyft.encode.annotate_encoding` for more information."""

    def annotate(self, hugr: Package | Hugr[Any]) -> None:
        """Annotate the current parameters of the architecture on the given HUGR in
        metadata. See `guppyft.encode.annotate` for more information."""


class EncodingArchitectureInstance(Protocol):
    """An architecture instance capable of providing a computational -> physical
    encoding, and op implementations for a logical -> physical lowering."""

    @overload
    def encode(self, pkg: Package, *, as_bytes: Literal[False] = False) -> Package: ...
    @overload
    def encode(self, pkg: Package, *, as_bytes: Literal[True]) -> bytes: ...
    @overload
    def encode(self, pkg: Package, *, as_bytes: bool) -> Package | bytes: ...
    def encode(self, pkg: Package, *, as_bytes: bool = False) -> Package | bytes:
        """Encode a computational package with this instance."""
        return self._encode(pkg, as_bytes=as_bytes)

    def _encode(self, pkg: Package, *, as_bytes: bool) -> Package | bytes: ...

    @overload
    def implement_ops(
        self, pkg: Package, *, as_bytes: Literal[False] = False
    ) -> Package: ...
    @overload
    def implement_ops(self, pkg: Package, *, as_bytes: Literal[True]) -> bytes: ...
    @overload
    def implement_ops(self, pkg: Package, *, as_bytes: bool) -> Package | bytes: ...
    def implement_ops(self, pkg: Package, *, as_bytes: bool = False) -> Package | bytes:
        """Implement logical ops in `pkg` using this instance's op implementations."""
        return self._implement_ops(pkg, as_bytes=as_bytes)

    def _implement_ops(self, pkg: Package, *, as_bytes: bool) -> Package | bytes: ...

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
        encoded_pkg = self.encode(pkg, as_bytes=True)
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


@overload
def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncodeSpec,
    *,
    passes: list[ComposablePass] | None = None,
    as_bytes: Literal[False] = False,
) -> Package: ...
@overload
def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncodeSpec,
    *,
    passes: list[ComposablePass] | None = None,
    as_bytes: Literal[True],
) -> bytes: ...
@overload
def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncodeSpec,
    *,
    passes: list[ComposablePass] | None = None,
    as_bytes: bool,
) -> Package | bytes: ...
def encode(
    hugr: Package | GuppyFunctionDefinition[[], None],
    spec: EncodeSpec,
    *,
    passes: list[ComposablePass] | None = None,
    as_bytes: bool = False,
) -> Package | bytes:
    """Encodes the given package (or Guppy function, directly compiled to a package for
    convenience) by applying four stages.

    1. running the given computational passes;
    2. lowering the operations in the package to logical operations and
       potentially performing static optimizations (e.g. resolving some qubit
       address assignments statically);
    3. running additional logical passes (e.g. inserting additional QEC cycles);
       and
    4. implementing the logical operations with physical gates.

    The returned runnable package is guaranteed to be semantically equivalent to the
    given one. The input package is not modified.

    Args:
        hugr: The package to encode, or a Guppy function for convenience.
        spec: See :class:`EncodeSpec`.
        passes: Computational passes to run on the given package. Defaults to one run
            of :class:`Normalize`.
        as_bytes: Whether to return the encoded package as bytes.

    Returns:
        The encoded runnable package, or its serialized representation when `as_bytes`
        is `True`.
    """
    pkg = hugr.compile_function() if isinstance(hugr, GuppyFunctionDefinition) else hugr

    assert len(pkg.modules) == 1, "Given package contains more than one module"
    assert not isinstance(pkg.modules[0].entrypoint_op(), Module), (
        "Cannot process module-rooted HUGRs"
    )

    # Passes return new HUGRs, but assigning them must not change the caller's lists.
    pkg = Package(modules=list(pkg.modules), extensions=list(pkg.extensions))

    # 1. Passes with computational -> computational
    for tket_pass in passes or [Normalize()]:
        pkg.modules[0] = tket_pass(pkg.modules[0], inplace=False)

    # 2. Lower computational -> logical
    if spec.compile is not None:
        pkg = spec.compile(pkg)

    # 3. Passes with logical -> logical
    for tket_pass in spec.logical_passes or []:
        pkg.modules[0] = tket_pass(pkg.modules[0], inplace=False)

    # 4. Lower logical -> physical
    if spec.implement_ops is not None:
        pkg_maybe_bytes = spec.implement_ops(pkg, as_bytes=as_bytes)
    else:
        pkg_maybe_bytes = pkg

    if isinstance(pkg_maybe_bytes, Package) and as_bytes:
        pkg_maybe_bytes = pkg_maybe_bytes.to_bytes()

    return pkg_maybe_bytes


def annotate_encoding(
    hugr: Package | Hugr[Any], encoding_name: str, params: Mapping[str, Any]
) -> None:
    """Annotate a HUGR package with encoding parameters.

    Args:
        hugr: The package or HUGR to annotate.
        encoding_name: The name of the encoding to annotate.
        params: The serializable encoding parameters.

    Raises:
        ValueError: If `params` cannot be serialized as JSON.
    """
    try:
        json.dumps(params, check_circular=True)
    except TypeError as e:
        raise ValueError("Could not serialize parameters") from e

    for module in hugr.modules if isinstance(hugr, Package) else [hugr]:
        module[module.module_root].metadata["qnt.nexus.compilation"] = {
            "schema_version": 1,
            "ft_encoding": {"name": encoding_name, "params": params},
        }
