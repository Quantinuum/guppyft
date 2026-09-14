from collections.abc import Mapping
from typing import Any

import pytest
from hugr import Hugr
from hugr.package import Package

from guppyft.encode import EncoderParams, annotate_encoding


def test_annotate_encoding() -> None:
    hugr1 = Hugr[Any]()
    hugr2 = Hugr[Any]()
    pkg = Package([hugr1, hugr2])
    hugr3 = Hugr[Any]()

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
    annotate_encoding(hugr3, CustomEncoderParams())

    assert hugr1[hugr1.module_root].metadata["guppyft.encoding"] == {
        "encoding": "my-custom-encoding",
        "params": {
            "my": "custom",
            "params": "that",
            "rock": "hard",
        },
    }
    assert (
        hugr1[hugr1.module_root].metadata["guppyft.encoding"]
        == hugr2[hugr2.module_root].metadata["guppyft.encoding"]
    )
    assert (
        hugr1[hugr1.module_root].metadata["guppyft.encoding"]
        == hugr3[hugr3.module_root].metadata["guppyft.encoding"]
    )


def test_annotate_encoding_not_json() -> None:
    hugr = Hugr[Any]()

    class FailingEncoderParams(EncoderParams):
        def encoding(self) -> str:
            return "my-failing-encoding"

        def params(self) -> Mapping[str, Any]:
            return {
                # Functions cannot be serialized with the standard JSON encoder
                "do-not": lambda x: x,
            }

    with pytest.raises(ValueError, match="Could not serialize parameters"):
        annotate_encoding(hugr, FailingEncoderParams())
