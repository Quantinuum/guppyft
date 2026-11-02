from typing import Any

import pytest
from hugr import Hugr
from hugr.package import Package

from guppyft.code.iceberg.encode import (
    DynamicQubitReuse,
    IcebergBuilder,
    IcebergQEDPolicy,
    InitStyle,
)


def test_iceberg_invalid_max_attempts() -> None:
    arch = IcebergBuilder()
    with pytest.raises(
        ValueError,
        match=r"Cannot set the maximum state prep RUS attempts lower than 1, 0 given",
    ):
        arch.with_state_prep_rus_attempts(0)
    with pytest.raises(
        ValueError,
        match=r"Cannot set the maximum state prep RUS attempts lower than 1, -5 given",
    ):
        arch.with_state_prep_rus_attempts(-5)


def test_iceberg_invalid_n_blocks() -> None:
    arch = IcebergBuilder()
    with pytest.raises(
        ValueError,
        match=r"Cannot set the number of blocks lower than 0, -1 given",
    ):
        arch.build(n_blocks=-1, block_size=4)


def test_iceberg_invalid_block_size() -> None:
    arch = IcebergBuilder()
    with pytest.raises(
        ValueError,
        match=r"Block size has to be even and at least 2, 0 given",
    ):
        arch.build(n_blocks=2, block_size=0)
    with pytest.raises(
        ValueError,
        match=r"Block size has to be even and at least 2, -2 given",
    ):
        arch.build(n_blocks=2, block_size=-2)
    with pytest.raises(
        ValueError,
        match=r"Block size has to be even and at least 2, 3 given",
    ):
        arch.build(n_blocks=2, block_size=3)


def test_annotate_iceberg_encoding() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    policy = IcebergQEDPolicy()
    policy.threshold = 42
    policy.costs.x = 1000.0
    arch = (
        IcebergBuilder()
        .with_init_style(InitStyle.HALF_DEPTH)
        .with_qed_policy(policy)
        .with_syndrome_extraction_during_measurement(True)
        .with_state_prep_rus_attempts(5)
        .with_dynamic_qubit_reuse(DynamicQubitReuse.disabled)
        .build(n_blocks=4, block_size=6)
    )
    arch.annotate(pkg)

    assert hugr[hugr.module_root].metadata["qnt.nexus.compilation"] == {
        "schema_version": 1,
        "ft_encoding": {
            "name": "iceberg",
            "params": {
                "schema_version": 1,
                "n_blocks": 4,
                "block_size": 6,
                "init_style": "half_depth",
                "qed_policy": {
                    "threshold": 42,
                    "costs": {
                        "idle": 0.0,
                        "all_x": 0.0,
                        "all_y": 0.0,
                        "all_z": 0.0,
                        "pauli_exp_all_x_except_at": 0.0,
                        "pauli_exp_all_z_except_at": 0.0,
                        "all_h": 0.0,
                        "x_with_all_but_one_z": 0.0,
                        "z_with_all_but_one_x": 0.0,
                        "cx_transversal": 0.0,
                        "yy_phase_intrablock": 0.0,
                        "xx_phase_interblock": 0.0,
                        "yy_phase_interblock": 0.0,
                        "alloc_dynq": 0.0,
                        "x": 1000.0,
                        "y": 0.0,
                        "z": 0.0,
                        "xx": 0.0,
                        "yy": 0.0,
                        "zz": 0.0,
                        "cx_intrablock": 0.0,
                        "cx_interblock": 0.0,
                        "fan_in": 0.0,
                        "fan_out": 0.0,
                        "swap": 0.0,
                        "rx": 0.0,
                        "rz": 0.0,
                        "all_rx": 0.0,
                        "all_ry": 0.0,
                        "all_rz": 0.0,
                        "all_but_one_rx": 0.0,
                        "all_but_one_rz": 0.0,
                        "xx_phase_intrablock": 0.0,
                        "zz_phase_intrablock": 0.0,
                        "zz_phase_interblock": 0.0,
                    },
                },
                "syndrome_during_measurement": True,
                "state_prep_rus_attempts": 5,
                "dynamic_qubit_reuse": "disabled",
            },
        },
    }


def test_annotated_policy_immutable() -> None:
    hugr = Hugr[Any]()
    pkg = Package([hugr])

    policy = IcebergQEDPolicy(threshold=2)
    policy.costs.x = 4.0
    instance = IcebergBuilder().with_qed_policy(policy).build(n_blocks=4, block_size=6)

    policy.threshold = 99
    policy.costs.x = 20.0
    instance.annotate(pkg)

    compilation = hugr[hugr.module_root].metadata["qnt.nexus.compilation"]
    policy_val = compilation["ft_encoding"]["params"]["qed_policy"]  # type: ignore[index,call-overload]
    assert policy_val["threshold"] == 2  # type: ignore[index,call-overload]
    assert policy_val["costs"]["x"] == 4.0  # type: ignore[index,call-overload]
