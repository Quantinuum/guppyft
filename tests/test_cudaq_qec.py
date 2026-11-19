from typing import no_type_check

import pytest
from guppylang import guppy
from hugr.cli import validate
from hugr.ops import ExtOp
from hugr.std.int import int_t
from hugr.tys import BoundedNatArg, ListArg

from guppyft.decoder import CudaQDecoder


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
