from collections.abc import Mapping
from typing import Any

from hugr import Hugr
from hugr.package import Package

from guppyft.encode import EncoderParams, annotate_encoding


def test_annotate_encoding() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    class CustomEncoderParams(EncoderParams):
        def encoding(self) -> str:
            return "my-custom-encoding"

        def params(self) -> Mapping[str, Any]:
            return {
                "my": "custom",
                "params": "that",
                "rock": "hard",
            }

    annotate_encoding(pkg, CustomEncoderParams())

    assert hugr[hugr.module_root].metadata["guppyft.encoding"] == {
        "encoding": "my-custom-encoding",
        "params": {
            "my": "custom",
            "params": "that",
            "rock": "hard",
        },
    }
