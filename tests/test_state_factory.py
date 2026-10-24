"""Tests for `PreBlock` and `StateFactory`."""

from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.defs import GuppyFunctionDefinition
from guppylang.std.builtins import array, comptime, output
from guppylang.std.collections import empty_queue
from guppylang.std.quantum import Measurement, measure, qubit, x

from guppyft.std import LogicalBlock
from guppyft.std.state_factory import PreBlock, StateFactory, flagged_pre_block


@guppy
@no_type_check
def _flag(value: bool) -> Measurement:
    q = qubit()
    if value:
        x(q)
    return measure(q)


@pytest.mark.parametrize(
    ("flags", "accepted"),
    [
        ([False, False, False], True),
        ([False, True, False], False),
        ([True, True, True], False),
    ],
)
def test_flagged_pre_block(flags: list[bool], accepted: bool) -> None:
    @guppy
    @no_type_check
    def main() -> None:
        blk = LogicalBlock(array(qubit() for _ in range(2)))
        flag_outcomes = array(_flag(f) for f in comptime(flags))
        result = flagged_pre_block(blk, flag_outcomes).force_check()
        if result.is_some():
            result.unwrap().discard()
            output("accepted", True)
        else:
            result.unwrap_nothing()
            output("accepted", False)

    shot = main.emulator(n_qubits=5).stabilizer_sim().run().collated_shots()[0]
    assert shot["accepted"] == [accepted]


@guppy.struct
class Attempts:
    """Resources counting the calls to the prep routine."""

    n: int


@guppy
@no_type_check
def _fail_twice(
    attempts: Attempts,
) -> PreBlock[LogicalBlock[1], array[Measurement, 1]]:
    attempts.n += 1
    blk = LogicalBlock(array(qubit() for _ in range(1)))
    return flagged_pre_block(blk, array(_flag(attempts.n <= 2)))


def _factory_program(max_attempts: int) -> GuppyFunctionDefinition[[], None]:
    @guppy
    @no_type_check
    def main() -> None:
        factory: StateFactory[LogicalBlock[1], array[Measurement, 1], Attempts, 1] = (
            StateFactory(_fail_twice, comptime(max_attempts), empty_queue())
        )
        attempts = Attempts(0)
        factory.get_state(attempts).discard()
        output("attempts", attempts.n)
        factory.discard()

    return main  # type: ignore[no-any-return]


def test_state_factory_passes_resources_and_retries() -> None:
    main = _factory_program(max_attempts=5)
    shot = main.emulator(n_qubits=2).stabilizer_sim().run().collated_shots()[0]
    assert shot["attempts"] == [3]


def test_state_factory_exits_when_out_of_attempts() -> None:
    main = _factory_program(max_attempts=2)
    result = main.emulator(n_qubits=2).stabilizer_sim().run()
    tags = result.collated_shots()[0].keys()
    assert "exit: StateFactory ran out of attempts!" in tags
