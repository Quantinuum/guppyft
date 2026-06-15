import pathlib

import pytest
from _pytest.capture import CaptureFixture
from pytest_snapshot.plugin import Snapshot

from tests.error.util import run_error_test

path = pathlib.Path(__file__).parent.resolve() / "global_op_errors"
files = [
    x
    for x in path.iterdir()
    if x.is_file() and x.suffix == ".py" and x.name != "__init__.py"
]


# Turn paths into strings, otherwise pytest doesn't display the names
files = [str(f) for f in files]


@pytest.mark.parametrize("file", files)
def test_global_op_errors(
    file: str, capsys: CaptureFixture[str], snapshot: Snapshot
) -> None:
    run_error_test(file, capsys, snapshot)
