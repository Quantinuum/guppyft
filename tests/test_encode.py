import pytest
from guppylang import guppy
from guppylang.std.platform import output
from guppylang.std.quantum import measure, qubit, x

from guppyft.encode import EncodeSpec, encode

from .utils.identity_code import identity_code_spec


@pytest.mark.parametrize("as_bytes", [False, True])
@pytest.mark.parametrize("implement", [False, True])
def test_encode_does_not_modify_package(as_bytes: bool, implement: bool) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        output("q", measure(q).read())

    pkg = main.with_minimal_opt().compile()
    module = pkg.modules[0]
    entrypoint = module.entrypoint
    before = pkg.to_str()
    spec = identity_code_spec(n_qubits=1) if implement else EncodeSpec()

    if as_bytes:
        encode(pkg, spec, as_bytes=True)
    else:
        encode(pkg, spec)

    assert pkg.to_str() == before
    assert pkg.modules[0] is module
    assert module.entrypoint == entrypoint
