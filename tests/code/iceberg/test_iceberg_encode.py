from dataclasses import fields
from typing import Any

import pytest
from hugr import Hugr
from hugr.package import Package

from guppyft.code.iceberg.encode import (
    DynamicQubitReuse,
    IcebergBuilder,
    IcebergInstance,
    IcebergQEDPolicy,
    RUSStateFactoryConf,
)
from guppyft.extensions import iceberg_ops


def test_iceberg_invalid_max_attempts() -> None:
    arch = IcebergBuilder()
    with pytest.raises(
        ValueError,
        match=r"Cannot set the size of the RUS state factory lower than 1, 0 given",
    ):
        arch.with_state_factory_conf(RUSStateFactoryConf(max_attempts=5, size=0))
    with pytest.raises(
        ValueError,
        match=r"Cannot set the size of the RUS state factory lower than 1, -5 given",
    ):
        arch.with_state_factory_conf(RUSStateFactoryConf(max_attempts=5, size=-5))
    with pytest.raises(
        ValueError,
        match=r"Cannot set the max attempts of the RUS state factory lower than 1, "
        r"0 given",
    ):
        arch.with_state_factory_conf(RUSStateFactoryConf(max_attempts=0, size=5))
    with pytest.raises(
        ValueError,
        match=r"Cannot set the max attempts of the RUS state factory lower than 1, "
        r"-5 given",
    ):
        arch.with_state_factory_conf(RUSStateFactoryConf(max_attempts=-5, size=5))


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
    for i, field in enumerate(fields(policy.costs)):
        policy.costs.__setattr__(field.name, i + 1.0)

    arch = (
        IcebergBuilder()
        .with_qed_policy(policy)
        .with_syndrome_extraction_during_measurement(True)
        .with_state_factory_conf(RUSStateFactoryConf(size=50, max_attempts=51))
        .with_dynamic_qubit_reuse(DynamicQubitReuse.disabled)
        .build(n_blocks=4, block_size=6)
    )
    arch.annotate(pkg)

    metadata = hugr[hugr.module_root].metadata["qnt.nexus.compilation"]
    assert isinstance(metadata, dict)
    arch_rec = IcebergBuilder.instance_from_params(metadata["ft_encoding"]["params"])
    assert arch == arch_rec

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
                        "idle": 1.0,
                        "alloc_dynq": 2.0,
                        "x": 3.0,
                        "y": 4.0,
                        "z": 5.0,
                        "x_all": 6.0,
                        "y_all": 7.0,
                        "z_all": 8.0,
                        "x_all_except_at": 9.0,
                        "z_all_except_at": 10.0,
                        "x_all_except_z_at": 11.0,
                        "z_all_except_x_at": 12.0,
                        "rx": 13.0,
                        "rz": 14.0,
                        "pauli_exp_x_all": 15.0,
                        "pauli_exp_y_all": 16.0,
                        "pauli_exp_z_all": 17.0,
                        "pauli_exp_x_all_except_at": 18.0,
                        "pauli_exp_z_all_except_at": 19.0,
                        "pauli_exp_x_all_except_z_at": 20.0,
                        "pauli_exp_z_all_except_x_at": 21.0,
                        "h_all": 22.0,
                        "cx_all": 23.0,
                        "cx_intrablock": 24.0,
                        "cx_interblock": 25.0,
                        "xx_intrablock": 26.0,
                        "yy_intrablock": 27.0,
                        "zz_intrablock": 28.0,
                        "xx_phase_intrablock": 29.0,
                        "xx_phase_interblock": 30.0,
                        "yy_phase_intrablock": 31.0,
                        "yy_phase_interblock": 32.0,
                        "zz_phase_intrablock": 33.0,
                        "zz_phase_interblock": 34.0,
                        "fan_in": 35.0,
                        "fan_out": 36.0,
                        "swap_intrablock": 37.0,
                    },
                },
                "syndrome_during_measurement": True,
                "state_factory": {
                    "size": 50,
                    "max_attempts": 51,
                },
                "dynamic_qubit_reuse": "disabled",
            },
        },
    }


def test_from_params_subclassing() -> None:
    """Assert that `from_params` invokes subclass builder constructors."""

    class IcebergSubInstance(IcebergInstance):
        def i_am(self) -> str:
            return f"I am the instance subclass with n_blocks={self._n_blocks}"

    class IcebergSubBuilder(IcebergBuilder):
        def build(self, *, n_blocks: int, block_size: int) -> IcebergInstance:
            return IcebergSubInstance(
                _n_blocks=n_blocks, _block_size=block_size, _options=self._options
            )

    arch = IcebergSubBuilder.instance_from_params(
        {
            "schema_version": 1,
            "n_blocks": 4,
            "block_size": 6,
        }
    )
    assert isinstance(arch, IcebergSubInstance)
    assert arch.i_am() == "I am the instance subclass with n_blocks=4"


def test_from_params_minimal() -> None:
    arch = IcebergBuilder.instance_from_params(
        {
            "schema_version": 1,
            "n_blocks": 4,
            "block_size": 6,
        }
    )

    assert arch == IcebergBuilder().build(n_blocks=4, block_size=6)


def test_from_params_defaults() -> None:
    """Assert that a key (e.g. the QED policy) can be partially specified."""
    arch = IcebergBuilder.instance_from_params(
        {
            "schema_version": 1,
            "n_blocks": 4,
            "block_size": 6,
            "qed_policy": {
                "costs": {
                    "x": 42,
                }
            },
        }
    )

    policy = IcebergQEDPolicy()
    policy.costs.x = 42

    assert arch == IcebergBuilder().with_qed_policy(policy).build(
        n_blocks=4, block_size=6
    )


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
