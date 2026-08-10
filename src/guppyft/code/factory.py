from dataclasses import dataclass
from typing import Generic, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, exit, panic
from guppylang.std.collections import Queue
from guppylang.std.lang import Function, owned
from guppylang.std.option import Option, nothing, some
from guppylang.std.quantum import Measurement, collect_measurements

from guppyft.code.util import LogicalBlock, array_any, qalloc_dirty

BLOCK_SIZE = guppy.nat_var("BLOCK_SIZE")
N_FLAGS = guppy.nat_var("N_FLAGS")
BATCH_SIZE = guppy.nat_var("BATCH_SIZE")


@dataclass(frozen=True)
class FactoryConf:
    """State factory configuration.

    Attributes:
        size: Maximum number of states to be produced in parallel.
        max_attempts: Maximum number of repeat-until-success attempts.
    """

    size: int
    max_attempts: int


@guppy.struct
@no_type_check
class PreBlock(Generic[BLOCK_SIZE, N_FLAGS]):  # type: ignore[misc]
    """Logical qubit that went through state preparation, but may not have succeeded.

    The measurement outcomes specifying if it succeeded have not been read. Hence,
    the runtime is not blocked by measurements, allowing multiple state preparation to
    occur in parallel.

    Args:
        BLOCK_SIZE: Number of physical qubits in the logical block.
        N_FLAGS: Size of the results array

    Attributes:
        logical_block (LogicalBlock[N]): The candidate logical block
        flag_outcomes (array[bool, N_FLAGS]): Array of measurement outcomes. Succeeds if
            all are `False`.
    """

    logical_block: LogicalBlock[BLOCK_SIZE]  # type: ignore[type-arg, valid-type]
    flag_outcomes: array[Measurement, N_FLAGS]  # type: ignore[valid-type]

    @guppy
    @no_type_check
    def force_check(
        self: PreBlock[BLOCK_SIZE, N_FLAGS] @ owned,
    ) -> Option[LogicalBlock[BLOCK_SIZE]]:
        """If preparation was successful, return the block, otherwise return `nothing`.

        Calling this forces the measurement of the flags to take place (if they had
        not already).
        """
        failed = array_any(collect_measurements(self.flag_outcomes))

        if failed:
            self.logical_block.discard()
            return nothing()
        else:
            return some(self.logical_block)


@guppy.struct
class StateFactory(Generic[BLOCK_SIZE, N_FLAGS, BATCH_SIZE]):  # type: ignore[misc]
    """State factory, making preparation attempts in parallel.

    Args:
        BLOCK_SIZE: Number of physical qubits in the logical block.
        N_FLAGS: Number of flag outcomes each `PreBlock` tracks.
        BATCH_SIZE: Number of states produced in the same batch.

    Attributes:
        prep_routine: Function to prepare a state.
        max_attempts: Maximum number of repeat-until-success attempts.
        batch: The Queue of elements in the batch. Provide an empty
          queue with `guppylang.std.collections.queue.empty_queue`.
    """

    prep_routine: Function[[], PreBlock[BLOCK_SIZE, N_FLAGS]]  # type: ignore[type-arg,valid-type]
    max_attempts: int
    batch: Queue[PreBlock[BLOCK_SIZE, N_FLAGS], BATCH_SIZE]  # type: ignore[type-arg,valid-type]

    @guppy
    @no_type_check
    def get_state(
        self: "StateFactory[BLOCK_SIZE, N_FLAGS, BATCH_SIZE]",
    ) -> LogicalBlock[BLOCK_SIZE]:
        """Parallel RUS preparation, up to `self.max_attempts` retries.

        All `BATCH_SIZE` state preparations may be run in parallel. If any of them
        succeeds, the state is returned. Surplus states are stored and can be fetched by
        subsequent calls to this function.
        """
        if BATCH_SIZE <= 0:
            panic("StateFactory: BATCH_SIZE must be greater than zero")

        for _ in range(self.max_attempts):
            # If empty, request a new batch
            if len(self.batch) == 0:
                for _ in range(BATCH_SIZE):
                    self.batch.push(self.prep_routine())

            # Pop an element from batch and check if it successfully prepared a state
            pre_block_prep = self.batch.pop()
            state = pre_block_prep.force_check()

            # If successful, early exit
            if state.is_some():
                return state.unwrap()
            else:
                state.unwrap_nothing()

        exit("StateFactory ran out of attempts!")
        return qalloc_dirty()  # Unreachable, but required by the Guppy checker

    @guppy
    @no_type_check
    def discard(self: "StateFactory[BLOCK_SIZE, N_FLAGS, BATCH_SIZE]" @ owned) -> None:
        for blk in self.batch:
            blk.logical_block.discard()
