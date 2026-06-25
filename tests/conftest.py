from collections.abc import Generator

import pytest
from guppylang_internals.diagnostic import DiagnosticsRenderer
from guppylang_internals.engine import DEF_STORE
from guppylang_internals.error import GuppyError


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,  # type: ignore[type-arg]
) -> Generator[None, pytest.TestReport]:
    """Render GuppyError diagnostics into the report before xdist serialises it."""
    outcome = yield
    report = outcome.get_result()

    if report.failed and isinstance(call.excinfo.value, GuppyError):
        renderer = DiagnosticsRenderer(DEF_STORE.sources)
        renderer.render_diagnostic(call.excinfo.value.error)
        rendered = "\n".join(renderer.buffer)
        report.sections.append(("Guppy compilation error", rendered))
