"""Guppy structs and definitions for state factories."""

from typing import Self, no_type_check

from guppylang import guppy
from guppylang.std.builtins import array, exit, nat, panic
from guppylang.std.collections import Queue
from guppylang.std.lang import Function, owned
from guppylang.std.option import Option, nothing, some
from guppylang.std.quantum import Measurement, collect_measurements

from ._logical_block import LogicalBlock

__all__ = [
    "NoResources",
    "PreBlock",
    "StateFactory",
    "flagged_pre_block",
]

BLOCK_SIZE = guppy.nat_var("BLOCK_SIZE")
N_FLAGS = guppy.nat_var("N_FLAGS")


@guppy
@no_type_check
def _array_any(arr: array[bool, BLOCK_SIZE]) -> bool:
    for i in range(BLOCK_SIZE):  # noqa: SIM110 # `all` is not yet supported by Guppy
        if arr[i]:
            return True
    return False


@guppy.struct
class PreBlock[Q, F]:
    """State that went through preparation, but may not have succeeded.

    The flags specifying whether it succeeded have not been checked. Hence, the runtime
    is not blocked by measurements, allowing multiple state preparations to occur in
    parallel.

    Type parameters:
        Q: Type of the prepared state, e.g. a logical block or logical qubit.
        F: Type of the flags, e.g. an array of unread measurements.

    Attributes:
        state: The candidate state.
        flags: Data used to decide whether the preparation succeeded.
        check_routine: Consumes the state and flags, applies any correction, and
            returns the state if the preparation succeeded, otherwise `nothing`.
        discard_routine: Consumes and discards the state and flags without checking.
    """

    state: Q
    flags: F
    check_routine: Function[[Q @ owned, F @ owned], Option[Q]]  # type: ignore[type-arg,valid-type]
    discard_routine: Function[[Q @ owned, F @ owned], None]  # type: ignore[type-arg,valid-type]

    @guppy
    @no_type_check
    def force_check(self: Self @ owned) -> Option[Q]:
        """If preparation was successful, return the state, otherwise `nothing`.

        Calling this forces the flags to be read (if they had not already).
        """
        return self.check_routine(self.state, self.flags)

    @guppy
    @no_type_check
    def discard(self: Self @ owned) -> None:
        """Discard the candidate state without checking it."""
        self.discard_routine(self.state, self.flags)


@guppy
@no_type_check
def _check_flags_zero(
    blk: LogicalBlock[BLOCK_SIZE] @ owned, flags: array[Measurement, N_FLAGS] @ owned
) -> Option[LogicalBlock[BLOCK_SIZE]]:
    if _array_any(collect_measurements(flags)):
        blk.discard()
        return nothing()
    return some(blk)


@guppy
@no_type_check
def _discard_flagged(
    blk: LogicalBlock[BLOCK_SIZE] @ owned, flags: array[Measurement, N_FLAGS] @ owned
) -> None:
    blk.discard()


@guppy
@no_type_check
def flagged_pre_block(
    blk: LogicalBlock[BLOCK_SIZE] @ owned, flags: array[Measurement, N_FLAGS] @ owned
) -> PreBlock[LogicalBlock[BLOCK_SIZE], array[Measurement, N_FLAGS]]:
    """Wrap a logical block with unread flag measurements into a `PreBlock`.

    The preparation succeeds if all flag outcomes are zero.
    """
    return PreBlock(blk, flags, _check_flags_zero, _discard_flagged)


@guppy.struct
class NoResources:
    """Resources for a `StateFactory` whose prep routine needs none."""


@guppy.struct
class StateFactory[Q, F, R, BATCH_SIZE: nat]:
    """State factory, making preparation attempts in parallel.

    Type parameters:
        Q: Type of the prepared state.
        F: Type of the flags of each `PreBlock`.
        R: Type of the resources passed to the prep routine, or `NoResources`.
        BATCH_SIZE: Number of states produced in the same batch.

    Attributes:
        prep_routine: Function to prepare a state, given the resources, e.g. another
            factory to draw input states from.
        max_attempts: Maximum number of repeat-until-success attempts.
        batch: The Queue of elements in the batch. Provide an empty
          queue with `guppylang.std.collections.queue.empty_queue`.
    """

    prep_routine: Function[[R], PreBlock[Q, F]]  # type: ignore[type-arg,valid-type,misc]
    max_attempts: int
    batch: Queue[PreBlock[Q, F], BATCH_SIZE]

    @guppy
    @no_type_check
    def get_state(self, resources: R) -> Q:
        """Parallel RUS preparation, up to `self.max_attempts` retries.

        All `BATCH_SIZE` state preparations may be run in parallel. If any of them
        succeeds, the state is returned. Surplus states are stored and can be fetched by
        subsequent calls to this function.

        Args:
            resources: Resources passed to each call of the prep routine.
        """
        if BATCH_SIZE <= 0:  # type: ignore[misc]
            panic("StateFactory: BATCH_SIZE must be greater than zero")

        for _ in range(self.max_attempts):
            # If empty, request a new batch
            if len(self.batch) == 0:
                for _ in range(BATCH_SIZE):  # type: ignore[misc]
                    self.batch.push(self.prep_routine(resources))

            # Pop an element from batch and check if it successfully prepared a state
            pre_block_prep = self.batch.pop()
            state = pre_block_prep.force_check()

            # If successful, early exit
            if state.is_some():
                return state.unwrap()
            else:
                state.unwrap_nothing()

        exit("StateFactory ran out of attempts!")
        # Unreachable, but required by the Guppy checker
        return self.batch.pop().force_check().unwrap()

    @guppy
    @no_type_check
    def discard(self: Self @ owned) -> None:
        """Discard all state-preparation candidates in the batch."""
        for pre_block in self.batch:
            pre_block.discard()
