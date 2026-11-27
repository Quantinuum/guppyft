from typing import no_type_check

import pytest
from guppylang import guppy
from guppylang.emulator.exceptions import EmulatorError
from guppylang.std.builtins import array, output
from hugr.cli import validate
from hugr.ops import ExtOp
from hugr.std.int import int_t
from hugr.tys import BoundedNatArg, ListArg

from guppyft.decoder.cudaq import CudaQDecoder, pack_int, unpack_int


@pytest.fixture(scope="module")
def decoder_gpu_ops() -> list[ExtOp]:
    @guppy
    @no_type_check
    def decode(syndrome: int) -> int:
        decoder = CudaQDecoder()
        decoder.enqueue_syndromes(0, 3, syndrome, 0)
        correction = decoder.get_corrections(0, 1, 1)
        decoder.reset_decoder(0)
        decoder.discard()
        return correction

    package = decode.compile_function()
    validate(package.to_bytes())
    return [
        op
        for module in package.modules
        for node in module.values()
        if isinstance(op := node.op, ExtOp)
        and op.op_def().get_extension().name == "tket.gpu"
    ]


def test_decoder_gpu_context(decoder_gpu_ops: list[ExtOp]) -> None:
    names = [op.op_def().name for op in decoder_gpu_ops]
    assert names.count("get_context") == 1
    assert names.count("dispose_context") == 1
    assert names.count("call") == 3
    assert names.count("read_result") == 3


@pytest.mark.parametrize(
    ("function_id", "input_count", "output_count"),
    [
        pytest.param(3644577968, 4, 0, id="enqueue_syndromes"),
        pytest.param(3961730203, 3, 1, id="get_corrections"),
        pytest.param(228606885, 1, 0, id="reset_decoder"),
    ],
)
def test_decoder_call_signature(
    decoder_gpu_ops: list[ExtOp],
    function_id: int,
    input_count: int,
    output_count: int,
) -> None:
    i64 = int_t(6).type_arg()
    signatures = [
        op.args for op in decoder_gpu_ops if op.op_def().name == "lookup_by_id"
    ]
    expected = [
        BoundedNatArg(function_id),
        ListArg([i64] * input_count),
        ListArg([i64] * output_count),
    ]
    assert expected in signatures


@pytest.mark.parametrize(
    ("width", "cases"),
    [
        pytest.param(
            3,
            [([True, False, False], 0b100), ([False, False, True], 0b001)],
            id="3-bits",
        ),
        pytest.param(
            64,
            [([True] + [False] * 63, -(2**63)), ([True] * 64, -1)],
            id="64-bits",
        ),
    ],
)
def test_pack_and_unpack_int(width: int, cases: list[tuple[list[bool], int]]) -> None:
    @guppy
    @no_type_check
    def convert(bits: array[bool, width], word: int) -> None:
        output("packed", pack_int(bits))
        output("unpacked", unpack_int[width](word))

    result = convert.emulator(1).run_per_shot(
        [{"bits": bits, "word": packed} for bits, packed in cases]
    )
    assert result.collated_shots() == [
        {"packed": [packed], "unpacked": [bits]} for bits, packed in cases
    ]


def test_unpack_int_ignores_high_bits() -> None:
    @guppy
    @no_type_check
    def unpack(word: int) -> None:
        output("bits", unpack_int[3](word))

    result = unpack.emulator(1).run_per_shot([{"word": 0b1100}])
    assert result.collated_shots() == [{"bits": [[True, False, False]]}]


def test_pack_and_unpack_int_at_zero_width() -> None:
    @guppy
    @no_type_check
    def convert(word: int) -> None:
        bits: array[bool, 0] = array()
        output("packed", pack_int(bits))
        output("width", len(unpack_int[0](word)))

    result = convert.emulator(1).run_per_shot([{"word": -1}])
    assert result.collated_shots() == [{"packed": [0], "width": [0]}]


def test_pack_int_rejects_more_than_64_bits() -> None:
    @guppy
    @no_type_check
    def pack_65_bits(bit: bool) -> None:
        output("packed", pack_int(array(bit for _ in range(65))))

    with pytest.raises(EmulatorError, match="bit arrays cannot exceed 64 bits"):
        pack_65_bits.emulator(1).run_per_shot([{"bit": True}])
