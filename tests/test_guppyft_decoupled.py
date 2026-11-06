import importlib.util
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest

empty_module = Path(__file__).parent / "resources/empty_module.py"
empty_module = str(empty_module.absolute().resolve())


def break_module(key: str) -> None:
    """Renders the module with the given key virtually unusable by replacing it with an
    empty module, causing every symbol import to fail with an ImportError."""
    spec = importlib.util.spec_from_file_location(key, empty_module)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module


@contextmanager
def broken_selene() -> Generator[None]:
    old_modules = sys.modules.copy()

    # Break all selene_sim, selene_core, and plugin imports
    for key in list(sys.modules.keys()):
        if key.startswith(("selene_sim", "selene_core")) or key.endswith("plugin"):
            break_module(key)

    # Purge cached guppylang imports
    for key in list(sys.modules.keys()):
        if key.startswith("guppylang"):
            del sys.modules[key]

    try:
        yield
    finally:
        # Reset imported modules
        sys.modules = old_modules


@pytest.mark.forked
def test_use_emulator() -> None:
    """Tests that using the emulator functionality raises an import error when imports
    are broken."""
    with broken_selene(), pytest.raises(ImportError, match=r"empty_module.py"):  # noqa: PT012
        from guppylang import guppy

        from guppyft.code.steane.encode import SteaneBuilder

        @guppy
        def f() -> None:
            pass

        _ = SteaneBuilder().build(n_blocks=1).emulator(f.compile(), n_qubits=1).run()


@pytest.mark.forked
def test_guppyft_decoupled_from_selene() -> None:
    """Tests that using the builder without emulator functionality can work without
    the selene dependencies."""

    with broken_selene():
        from guppylang import guppy

        from guppyft.code.steane.encode import SteaneBuilder

        @guppy
        def f() -> None:
            pass

        _ = SteaneBuilder().build(n_blocks=1).encode(f.compile())
