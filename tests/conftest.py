from collections.abc import Callable
from functools import cache

import pytest

from guppyft.code.steane.encode import SteaneBuilder, SteaneInstance


@pytest.fixture(scope="session")
def make_steane_instance() -> Callable[[int], SteaneInstance]:
    @cache
    def build(n_blocks: int) -> SteaneInstance:
        return SteaneBuilder().build(n_blocks=n_blocks)

    return build
