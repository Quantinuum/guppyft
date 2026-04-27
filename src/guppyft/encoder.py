import itertools
from typing import no_type_check

from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from hugr.package import Package
from hugr.passes.composable import ComposablePass
from tket.passes import NormalizeGuppy

from guppyft._bindings import RsHugr
from guppyft._bindings import _replace_ops as _replace_ops_binding
from guppyft._util import link_name
from guppyft.spec import EncoderSpec, OpReplacements


def _replace_ops(hugr: Package, ops: OpReplacements) -> Package:
    rs_hugr = RsHugr.from_bytes(hugr.modules[0].to_bytes())

    rs_ops = {
        key: (
            func_opt
            if func_opt is None
            else RsHugr.from_bytes(func_opt.compile_function().modules[0].to_bytes()),
            name,
        )
        for key, (func_opt, name) in ops
    }

    _replace_ops_binding(rs_hugr, rs_ops)

    return Package.from_bytes(rs_hugr.to_bytes())


def encode(
    func: GuppyFunctionDefinition[[], None],
    spec: EncoderSpec,
    *,
    passes: list[ComposablePass] | None = None,
) -> Package:
    """
    Encodes the given function using the given spec by replacing all operations in the
    program with function calls to the functions in `spec.ops`.

    :param func: The function to encode. Must take no arguments and return `None`.
    :param spec: The spec for the encoding. See `EncoderSpec` for details.
    :param passes: Tket passes to run on the unencoded program, before passes from the
        spec. The default is a single run of `tket.passes.NormalizeGuppy`.
    :return: The compiled, encoded function as an executable HUGR package.
    """
    # Compile unencoded program with entrypoint since NormalizeGuppy needs it
    func_pkg: Package = func.compile()

    # Run all tket passes
    if passes is None:
        passes = [NormalizeGuppy()]
    for tket_pass in itertools.chain(passes, spec.tket_passes):
        tket_pass(func_pkg.modules[0])

    # Reset entrypoint to mark module as non-executable to avoid conflicts
    func_pkg.modules[0].entrypoint = func_pkg.modules[0].module_root
    # Run rewrite, replacing ops with function calls to the functions in `spec.ops`
    func_pkg = _replace_ops(func_pkg, spec.ops)

    # Build, compile, and link wrapper program
    @guppy.declare(link_name=link_name(func))
    @no_type_check
    def func_decl() -> None: ...

    wrapper = spec.build_wrapper(func_decl)
    pkg: Package = wrapper.compile()
    pkg = pkg.link(func_pkg, *spec.libs)
    assert isinstance(pkg, Package)  # Assert type for type checker

    return pkg
