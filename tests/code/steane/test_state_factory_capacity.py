import pytest
from guppylang import guppy
from guppylang.emulator.exceptions import EmulatorError
from guppylang.std.builtins import array
from guppylang.std.platform import output
from guppylang.std.quantum import collect_measurements, measure_array, qubit, x
from selene_sim.backends.bundled_simulators import Coinflip

from guppyft.code.steane.encode import RUSStateFactoryConf, SteaneBuilder
from guppyft.code.steane.logical import Qubit, prep_t_state


@pytest.mark.parametrize("factory_size", [1, 2])
def test_state_factory_respects_shared_block_limit(factory_size: int) -> None:
    @guppy
    def main() -> None:
        qubits = array(qubit() for _ in range(3))
        x(qubits[1])
        output("blocks", collect_measurements(measure_array(qubits)))

    n_blocks = 3
    # Three seven-qubit blocks, plus one verification ancilla per preparation in
    # the largest batch. Both cases get the same physical capacity. There is no
    # room for the fourth block produced by a second full batch of size two.
    n_qubits = 7 * n_blocks + 1
    result = (
        SteaneBuilder()
        .with_zero_factory_conf(RUSStateFactoryConf(size=factory_size, max_attempts=5))
        .build(n_blocks=n_blocks)
        .emulator(main.compile(), n_qubits=n_qubits)
        .stabilizer_sim()
        .run()
        .collated_shots()
    )

    assert result == [{"blocks": [[0, 1, 0]]}]


def test_block_limit_does_not_reserve_preparation_ancillas() -> None:
    @guppy
    def main() -> None:
        blocks = array(qubit() for _ in range(3))
        output("blocks", collect_measurements(measure_array(blocks)))

    n_blocks = 3
    # The physical budget holds exactly three data blocks, without ancilla space.
    # With two blocks live, the final preparation takes the peak qubits to 22.
    n_qubits = 7 * n_blocks
    emulator = (
        SteaneBuilder()
        .with_zero_factory_conf(RUSStateFactoryConf(size=1, max_attempts=5))
        .build(n_blocks=n_blocks)
        .emulator(main.compile(), n_qubits=n_qubits)
        .stabilizer_sim()
    )

    with pytest.raises(
        EmulatorError, match=r"Panic \(#1001\): No more qubits available to allocate\."
    ):
        emulator.run()


def test_zero_factory_exits_when_no_blocks_are_available() -> None:
    @guppy
    def main() -> None:
        blocks = array(Qubit(), prep_t_state(), Qubit())
        for block in blocks:
            block.free()

    # The first zero state and the two-candidate magic batch fill all three slots.
    # A logical address remains free, but the empty zero factory cannot refill.
    result = (
        SteaneBuilder()
        .with_zero_factory_conf(RUSStateFactoryConf(size=1, max_attempts=5))
        .with_magic_factory_conf(RUSStateFactoryConf(size=2, max_attempts=5))
        .build(n_blocks=3)
        .emulator(main.compile(), n_qubits=40)
        .with_simulator(Coinflip(bias=0.0))
        .run()
        .collated_shots()
    )

    assert result == [{"exit: StateFactory: no free blocks available": [1]}]
