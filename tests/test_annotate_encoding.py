from typing import Any

import pytest
from hugr import Hugr
from hugr.package import Package

from guppyft.encode import annotate_encoding


def test_annotate_encoding() -> None:
    hugr1 = Hugr[Any]()
    hugr2 = Hugr[Any]()
    pkg = Package([hugr1, hugr2])
    hugr3 = Hugr[Any]()

    params = {
        "my": "custom",
        "params": "that",
        "rock": "hard",
    }
    annotate_encoding(pkg, "my-custom-encoding", params)
    annotate_encoding(hugr3, "my-custom-encoding", params)

    assert hugr1[hugr1.module_root].metadata["qnt.nexus.compilation"] == {
        "schema_version": 1,
        "encoding": {
            "name": "my-custom-encoding",
            "params": {
                "my": "custom",
                "params": "that",
                "rock": "hard",
            },
        },
    }
    assert (
        hugr1[hugr1.module_root].metadata["qnt.nexus.compilation"]
        == hugr2[hugr2.module_root].metadata["qnt.nexus.compilation"]
    )
    assert (
        hugr1[hugr1.module_root].metadata["qnt.nexus.compilation"]
        == hugr3[hugr3.module_root].metadata["qnt.nexus.compilation"]
    )


def test_annotate_encoding_not_json() -> None:
    hugr = Hugr[Any]()
    params = {
        # Functions cannot be serialized with the standard JSON encoder
        "do-not": lambda x: x,
    }

    with pytest.raises(ValueError, match="Could not serialize parameters"):
        annotate_encoding(hugr, "my-failing-encoding", params)
