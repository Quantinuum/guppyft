import pytest
from guppylang import guppy
from guppylang.std.platform import output
from guppylang.std.quantum import measure, qubit, x

from guppyft.encode import EncodeSpec, encode

from .utils.identity_code import IdentityBuilder


@pytest.mark.parametrize("as_bytes", [False, True])
@pytest.mark.parametrize("empty_spec", [False, True])
def test_encode_does_not_modify_package(as_bytes: bool, empty_spec: bool) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        output("q", measure(q).read())

    pkg = main.with_minimal_opt().compile()
    [module] = pkg.modules
    entrypoint = module.entrypoint
    before = pkg.to_str()

    if empty_spec:
        encode(pkg, EncodeSpec(), as_bytes=as_bytes)
    else:
        IdentityBuilder().build(n_qubits=1).encode(pkg, as_bytes=as_bytes)

    assert pkg.to_str() == before
    [module_after] = pkg.modules
    assert module_after is module
    assert module.entrypoint == entrypoint
