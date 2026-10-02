# ruff: noqa: INP001
"""Execute ``testcode`` directives found in public API docstrings."""

from __future__ import annotations

import ast
import os
import runpy
import tempfile
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).parent.parent
SOURCE_ROOT = ROOT / "src" / "guppyft"


def _public_docstrings(node: ast.AST) -> Iterator[tuple[str, int, str]]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not child.name.startswith("_"):
                docstring = ast.get_docstring(child, clean=True)
                if docstring is not None:
                    yield child.name, child.lineno, docstring
            yield from _public_docstrings(child)


def _testcode_blocks(docstring: str) -> Iterator[str]:
    lines = docstring.splitlines(keepends=True)
    line_index = 0
    while line_index < len(lines):
        if not lines[line_index].lstrip().startswith(".. testcode::"):
            line_index += 1
            continue

        line_index += 1
        code_lines: list[str] = []
        while line_index < len(lines):
            line = lines[line_index]
            if line.strip() and not line[0].isspace():
                break
            if line.lstrip().startswith(":") and not code_lines:
                line_index += 1
                continue
            code_lines.append(line)
            line_index += 1

        code = textwrap.dedent("".join(code_lines)).strip()
        if code:
            yield code + "\n"


def main() -> None:
    """Run every docstring ``testcode`` block from the package source tree."""
    os.chdir(ROOT)
    example_number = 0
    for source_path in SOURCE_ROOT.rglob("*.py"):
        module = ast.parse(source_path.read_text(), filename=source_path)
        for object_name, line_number, docstring in _public_docstrings(module):
            for snippet in _testcode_blocks(docstring):
                example_number += 1
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    prefix="guppyft-docstring-",
                    delete=False,
                ) as example_file:
                    example_file.write(snippet)
                    example_path = Path(example_file.name)
                try:
                    runpy.run_path(
                        str(example_path),
                        run_name=f"__guppyft_docstring_example_{example_number}__",
                    )
                except Exception as error:
                    location = f"{source_path.relative_to(ROOT)}:{line_number}"
                    raise RuntimeError(
                        f"testcode example for {object_name} failed at {location}"
                    ) from error
                finally:
                    example_path.unlink()


if __name__ == "__main__":
    main()
