"""Read marimo examples through MyST-NB without storing Jupyter notebooks."""  # noqa: INP001

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

import nbformat


def read(source: str) -> nbformat.NotebookNode:
    """Export marimo source for Sphinx to render, cache, and execute as usual."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / "notebook.py"
        path.write_text(source, encoding="utf-8")
        result = subprocess.run(  # noqa: S603 -- only exports repository-owned source
            [sys.executable, "-m", "marimo", "export", "ipynb", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    notebook = nbformat.reads(result.stdout, as_version=4)  # type: ignore[no-untyped-call]
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    return cast("nbformat.NotebookNode", notebook)
