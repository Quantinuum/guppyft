import pytest
from guppylang import guppy
from guppylang.std.platform import output
from guppylang.std.quantum import measure, qubit, x
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from guppyft.encode import EncodeSpec, encode

from .utils.identity_code import IdentityBuilder
from .utils.tracing import TraceStructure, get_trace_structure


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
        IdentityBuilder.new(n_qubits=1).build().encode(pkg, as_bytes=as_bytes)

    assert pkg.to_str() == before
    [module_after] = pkg.modules
    assert module_after is module
    assert module.entrypoint == entrypoint


@pytest.mark.parametrize("as_bytes", [False, True])
def test_encode_traces(monkeypatch: pytest.MonkeyPatch, as_bytes: bool) -> None:
    @guppy
    def main() -> None:
        q = qubit()
        x(q)
        output("q", measure(q).read())

    instance = IdentityBuilder.new(n_qubits=1).build()
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Real global tracer provider can only be set once, so patch the getter here
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)

    try:
        encode(main, instance._spec, as_bytes=as_bytes)
        spans = exporter.get_finished_spans()
    finally:
        provider.shutdown()

    implementation: TraceStructure = [
        ("serialise_user_pkg", []),
        ("implement", []),
        ("build_wrapper", []),
        ("serialise_libs", []),
        ("link_libs", []),
    ]
    if not as_bytes:
        implementation.append(("deserialise_product", []))

    assert get_trace_structure(spans) == [
        ("compile_function", []),
        ("computational_passes", []),
        ("logical_compilation", []),
        ("logical_passes", []),
        (
            "implement_ops",
            [
                ("spec_gen", []),
                ("implement_ops_invoke", implementation),
            ],
        ),
    ]
