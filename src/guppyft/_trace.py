from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace


@contextmanager
def tracing(name: str) -> Iterator[None]:
    with trace.get_tracer("guppyft").start_as_current_span(name):
        yield
