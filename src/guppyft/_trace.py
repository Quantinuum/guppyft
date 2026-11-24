from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Tracer


def _init_tracer() -> Tracer:
    return trace.get_tracer(__name__)


@contextmanager
def tracing(name: str) -> Iterator[None]:
    with trace.get_tracer(__name__).start_as_current_span(name):
        yield
