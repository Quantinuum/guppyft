from dataclasses import fields
from typing import Any

import pytest
from hugr import Hugr
from hugr.package import Package

from guppyft.code.iceberg.encode import (
    DynamicQubitReuse,
    IcebergBuilder,
    IcebergQEDPolicy,
)
from guppyft.extensions import iceberg_ops


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
                "qed_policy": {
                    "threshold": 42,
                    "costs": {
                        "idle": 0.0,
                        "alloc_dynq": 0.0,
                        "x": 1000.0,
                        "y": 0.0,
                        "z": 0.0,
                        "x_all": 0.0,
                        "y_all": 0.0,
                        "z_all": 0.0,
                        "x_all_except_at": 0.0,
                        "z_all_except_at": 0.0,
                        "x_all_except_z_at": 0.0,
                        "z_all_except_x_at": 0.0,
                        "rx": 0.0,
                        "rz": 0.0,
                        "pauli_exp_x_all": 0.0,
                        "pauli_exp_y_all": 0.0,
                        "pauli_exp_z_all": 0.0,
                        "pauli_exp_x_all_except_at": 0.0,
                        "pauli_exp_z_all_except_at": 0.0,
                        "pauli_exp_x_all_except_z_at": 0.0,
                        "pauli_exp_z_all_except_x_at": 0.0,
                        "h_all": 0.0,
                        "cx_all": 0.0,
                        "cx_intrablock": 0.0,
                        "cx_interblock": 0.0,
                        "xx_intrablock": 0.0,
                        "yy_intrablock": 0.0,
                        "zz_intrablock": 0.0,
                        "xx_phase_intrablock": 0.0,
                        "xx_phase_interblock": 0.0,
                        "yy_phase_intrablock": 0.0,
                        "yy_phase_interblock": 0.0,
                        "zz_phase_intrablock": 0.0,
                        "zz_phase_interblock": 0.0,
                        "fan_in": 0.0,
                        "fan_out": 0.0,
                        "swap_intrablock": 0.0,
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


def test_costs_have_existing_ops() -> None:
    costs = {cost.name for cost in fields(IcebergQEDPolicy.OperationCosts)}
    assert "idle" in costs
    costs.remove("idle")

    ops = {
        op
        for op in iceberg_ops().operations
        if (
            (("dynq" not in op and "alloc" not in op) or op == "alloc_dynq")
            and "measure" not in op
            and op
            not in ("free", "check_pre_block", "borrow", "restore", "take", "put")
        )
    }

    assert costs == ops
