from collections import defaultdict
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.trace import SpanContext

type TraceStructure = list[tuple[str, TraceStructure]]


def get_trace_structure(spans: Sequence[ReadableSpan]) -> TraceStructure:
    """Return span names and children in start order, omitting IDs and timings."""
    children: dict[tuple[int, int] | None, list[ReadableSpan]] = defaultdict(list)

    def key(context: SpanContext | None) -> tuple[int, int] | None:
        return None if context is None else (context.trace_id, context.span_id)

    def start_time(span: ReadableSpan) -> int:
        assert span.start_time is not None
        return span.start_time

    for span in sorted(spans, key=start_time):
        assert span.context is not None
        children[key(span.parent)].append(span)

    def structure(parent: SpanContext | None) -> TraceStructure:
        return [
            (span.name, structure(span.context))
            for span in children.get(key(parent), [])
        ]

    return structure(None)
