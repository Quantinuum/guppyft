"""Iceberg code extension."""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.tys import BoundedNatArg, ExtType

from ._util import load_extension


class IcebergTypesExtension:
    """Extension providing the Iceberg codeblock."""

    def __call__(self) -> Extension:
        """Returns the Iceberg types extension"""
        return load_extension("guppyft.iceberg.types")

    @functools.cached_property
    def iceberg_block_def(self) -> TypeDef:
        """An Iceberg code block.

        This is the generic type definition. For the instantiated type, see
        `iceberg_block`.
        """
        return self().get_type("block")

    def iceberg_block(self, k: int) -> ExtType:
        """An Iceberg code block.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.iceberg_block_def.instantiate([BoundedNatArg(k)])


class IcebergOpsExtension:
    """Extension providing the Iceberg logical operations."""

    def __call__(self) -> Extension:
        """Returns the Iceberg ops extension"""
        return load_extension("guppyft.iceberg.ops")

    # x

    @functools.cached_property
    def x_def(self) -> OpDef:
        """Apply an X gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `x`."""
        return self().get_op("x")

    def x(self, k: int, i: int) -> ExtOp:
        """Apply an X gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.x_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def x_d_def(self) -> OpDef:
        """Apply an X gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `x_d`."""
        return self().get_op("x_d")

    def x_d(self, k: int) -> ExtOp:
        """Apply an X gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.x_d_def.instantiate([BoundedNatArg(k)])

    # z

    @functools.cached_property
    def z_def(self) -> OpDef:
        """Apply a Z gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `z`."""
        return self().get_op("z")

    def z(self, k: int, i: int) -> ExtOp:
        """Apply a Z gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.z_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def z_d_def(self) -> OpDef:
        """Apply a Z gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `z_d`."""
        return self().get_op("z_d")

    def z_d(self, k: int) -> ExtOp:
        """Apply a Z gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.z_d_def.instantiate([BoundedNatArg(k)])

    # xx

    @functools.cached_property
    def xx_def(self) -> OpDef:
        """Apply an X gate to two qubits.

        This is the generic operation definition. For the instantiated operation, see
        `xx`."""
        return self().get_op("xx")

    def xx(self, k: int, i: int, j: int) -> ExtOp:
        """Apply an X gate to two qubits.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.xx_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def xx_d_def(self) -> OpDef:
        """Apply an X gate to two qubits with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `xx_d`."""
        return self().get_op("xx_d")

    def xx_d(self, k: int) -> ExtOp:
        """Apply an X gate to two qubits with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.xx_d_def.instantiate([BoundedNatArg(k)])

    # yy

    @functools.cached_property
    def yy_def(self) -> OpDef:
        """Apply a Y gate to two qubits.

        This is the generic operation definition. For the instantiated operation, see
        `yy`."""
        return self().get_op("yy")

    def yy(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a Y gate to two qubits.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.yy_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def yy_d_def(self) -> OpDef:
        """Apply a Y gate to two qubits with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `yy_d`."""
        return self().get_op("yy_d")

    def yy_d(self, k: int) -> ExtOp:
        """Apply a Y gate to two qubits with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.yy_d_def.instantiate([BoundedNatArg(k)])

    # zz

    @functools.cached_property
    def zz_def(self) -> OpDef:
        """Apply a Z gate to two qubits.

        This is the generic operation definition. For the instantiated operation, see
        `zz`."""
        return self().get_op("zz")

    def zz(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a Z gate to two qubits.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.zz_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def zz_d_def(self) -> OpDef:
        """Apply a Z gate to two qubits with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `zz_d`."""
        return self().get_op("zz_d")

    def zz_d(self, k: int) -> ExtOp:
        """Apply a Z gate to two qubits with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.zz_d_def.instantiate([BoundedNatArg(k)])

    # all_but_one_x

    @functools.cached_property
    def all_but_one_x_def(self) -> OpDef:
        """Apply an X gate to all but one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_x`."""
        return self().get_op("all_but_one_x")

    def all_but_one_x(self, k: int, i: int) -> ExtOp:
        """Apply an X gate to all but one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit omitted.
        """
        return self.all_but_one_x_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def all_but_one_x_d_def(self) -> OpDef:
        """Apply an X gate to all but one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_x_d`."""
        return self().get_op("all_but_one_x_d")

    def all_but_one_x_d(self, k: int) -> ExtOp:
        """Apply an X gate to all but one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_but_one_x_d_def.instantiate([BoundedNatArg(k)])

    # all_but_one_z

    @functools.cached_property
    def all_but_one_z_def(self) -> OpDef:
        """Apply a Z gate to all but one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_z`."""
        return self().get_op("all_but_one_z")

    def all_but_one_z(self, k: int, i: int) -> ExtOp:
        """Apply a Z gate to all but one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit omitted.
        """
        return self.all_but_one_z_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def all_but_one_z_d_def(self) -> OpDef:
        """Apply a Z gate to all but one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_z_d`."""
        return self().get_op("all_but_one_z_d")

    def all_but_one_z_d(self, k: int) -> ExtOp:
        """Apply a Z gate to all but one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_but_one_z_d_def.instantiate([BoundedNatArg(k)])

    # all_x

    @functools.cached_property
    def all_x_def(self) -> OpDef:
        """Apply an X gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_x`."""
        return self().get_op("all_x")

    def all_x(self, k: int) -> ExtOp:
        """Apply an X gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_x_def.instantiate([BoundedNatArg(k)])

    # all_y

    @functools.cached_property
    def all_y_def(self) -> OpDef:
        """Apply a Y gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_y`."""
        return self().get_op("all_y")

    def all_y(self, k: int) -> ExtOp:
        """Apply a Y gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_y_def.instantiate([BoundedNatArg(k)])

    # all_z

    @functools.cached_property
    def all_z_def(self) -> OpDef:
        """Apply a Z gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_z`."""
        return self().get_op("all_z")

    def all_z(self, k: int) -> ExtOp:
        """Apply a Z gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_z_def.instantiate([BoundedNatArg(k)])

    # x_with_all_but_one_z

    @functools.cached_property
    def x_with_all_but_one_z_def(self) -> OpDef:
        """Apply an X gate to one qubit and a Z to the rest.

        This is the generic operation definition. For the instantiated operation, see
        `x_with_all_but_one_z`."""
        return self().get_op("x_with_all_but_one_z")

    def x_with_all_but_one_z(self, k: int, i: int) -> ExtOp:
        """Apply an X gate to one qubit and a Z to the rest.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.x_with_all_but_one_z_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i)]
        )

    @functools.cached_property
    def x_with_all_but_one_z_d_def(self) -> OpDef:
        """Apply an X gate to one qubit and a Z to the rest with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `x_with_all_but_one_z_d`."""
        return self().get_op("x_with_all_but_one_z_d")

    def x_with_all_but_one_z_d(self, k: int) -> ExtOp:
        """Apply an X gate to one qubit and a Z to the rest with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.x_with_all_but_one_z_d_def.instantiate([BoundedNatArg(k)])

    # z_with_all_but_one_x

    @functools.cached_property
    def z_with_all_but_one_x_def(self) -> OpDef:
        """Apply a Z gate to one qubit and an X to the rest.

        This is the generic operation definition. For the instantiated operation, see
        `z_with_all_but_one_x`."""
        return self().get_op("z_with_all_but_one_x")

    def z_with_all_but_one_x(self, k: int, i: int) -> ExtOp:
        """Apply a Z gate to one qubit and an X to the rest.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.z_with_all_but_one_x_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i)]
        )

    @functools.cached_property
    def z_with_all_but_one_x_d_def(self) -> OpDef:
        """Apply a Z gate to one qubit and an X to the rest with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `z_with_all_but_one_x_d`."""
        return self().get_op("z_with_all_but_one_x_d")

    def z_with_all_but_one_x_d(self, k: int) -> ExtOp:
        """Apply a Z gate to one qubit and an X to the rest with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.z_with_all_but_one_x_d_def.instantiate([BoundedNatArg(k)])

    # fan_out

    @functools.cached_property
    def fan_out_def(self) -> OpDef:
        """Fan out from one qubit to the rest.

        This is the generic operation definition. For the instantiated operation, see
        `fan_out`."""
        return self().get_op("fan_out")

    def fan_out(self, k: int, i: int) -> ExtOp:
        """Fan out from one qubit to the rest.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.fan_out_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def fan_out_d_def(self) -> OpDef:
        """Fan out from one qubit to the rest with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `fan_out_d`."""
        return self().get_op("fan_out_d")

    def fan_out_d(self, k: int) -> ExtOp:
        """Fan out from one qubit to the rest with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.fan_out_d_def.instantiate([BoundedNatArg(k)])

    # fan_in

    @functools.cached_property
    def fan_in_def(self) -> OpDef:
        """Fan in to one qubit from the rest.

        This is the generic operation definition. For the instantiated operation, see
        `fan_in`."""
        return self().get_op("fan_in")

    def fan_in(self, k: int, i: int) -> ExtOp:
        """Fan in to one qubit from the rest.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.fan_in_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def fan_in_d_def(self) -> OpDef:
        """Fan in to one qubit from the rest with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `fan_in_d`."""
        return self().get_op("fan_in_d")

    def fan_in_d(self, k: int) -> ExtOp:
        """Fan in to one qubit from the rest with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.fan_in_d_def.instantiate([BoundedNatArg(k)])

    # rx

    @functools.cached_property
    def rx_def(self) -> OpDef:
        """Apply an Rx gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `rx`."""
        return self().get_op("rx")

    def rx(self, k: int, i: int) -> ExtOp:
        """Apply an Rx gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.rx_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def rx_d_def(self) -> OpDef:
        """Apply an Rx gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `rx_d`."""
        return self().get_op("rx_d")

    def rx_d(self, k: int) -> ExtOp:
        """Apply an Rx gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.rx_d_def.instantiate([BoundedNatArg(k)])

    # rz

    @functools.cached_property
    def rz_def(self) -> OpDef:
        """Apply an Rz gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `rz`."""
        return self().get_op("rz")

    def rz(self, k: int, i: int) -> ExtOp:
        """Apply an Rz gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.rz_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def rz_d_def(self) -> OpDef:
        """Apply an Rz gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `rz_d`."""
        return self().get_op("rz_d")

    def rz_d(self, k: int) -> ExtOp:
        """Apply an Rz gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.rz_d_def.instantiate([BoundedNatArg(k)])

    # all_rx

    @functools.cached_property
    def all_rx_def(self) -> OpDef:
        """Apply an Rx gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_rx`."""
        return self().get_op("all_rx")

    def all_rx(self, k: int) -> ExtOp:
        """Apply an Rx gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_rx_def.instantiate([BoundedNatArg(k)])

    # all_ry

    @functools.cached_property
    def all_ry_def(self) -> OpDef:
        """Apply an Ry gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_ry`."""
        return self().get_op("all_ry")

    def all_ry(self, k: int) -> ExtOp:
        """Apply an Ry gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_ry_def.instantiate([BoundedNatArg(k)])

    # all_rz

    @functools.cached_property
    def all_rz_def(self) -> OpDef:
        """Apply an Rz gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_rz`."""
        return self().get_op("all_rz")

    def all_rz(self, k: int) -> ExtOp:
        """Apply an Rz gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_rz_def.instantiate([BoundedNatArg(k)])

    # all_but_one_rx

    @functools.cached_property
    def all_but_one_rx_def(self) -> OpDef:
        """Apply an Rx gate to all but one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_rx`."""
        return self().get_op("all_but_one_rx")

    def all_but_one_rx(self, k: int, i: int) -> ExtOp:
        """Apply an Rx gate to all but one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit omitted.
        """
        return self.all_but_one_rx_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def all_but_one_rx_d_def(self) -> OpDef:
        """Apply an Rx gate to all but one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_rx_d`."""
        return self().get_op("all_but_one_rx_d")

    def all_but_one_rx_d(self, k: int) -> ExtOp:
        """Apply an Rx gate to all but one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_but_one_rx_d_def.instantiate([BoundedNatArg(k)])

    # all_but_one_rz

    @functools.cached_property
    def all_but_one_rz_def(self) -> OpDef:
        """Apply an Rz gate to all but one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_rz`."""
        return self().get_op("all_but_one_rz")

    def all_but_one_rz(self, k: int, i: int) -> ExtOp:
        """Apply an Rz gate to all but one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit omitted.
        """
        return self.all_but_one_rz_def.instantiate([BoundedNatArg(k), BoundedNatArg(i)])

    @functools.cached_property
    def all_but_one_rz_d_def(self) -> OpDef:
        """Apply an Rz gate to all but one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `all_but_one_rz_d`."""
        return self().get_op("all_but_one_rz_d")

    def all_but_one_rz_d(self, k: int) -> ExtOp:
        """Apply an Rz gate to all but one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_but_one_rz_d_def.instantiate([BoundedNatArg(k)])

    # all_h

    @functools.cached_property
    def all_h_def(self) -> OpDef:
        """Apply an H gate to all qubits.

        This is the generic operation definition. For the instantiated operation, see
        `all_h`."""
        return self().get_op("all_h")

    def all_h(self, k: int) -> ExtOp:
        """Apply an H gate to all qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.all_h_def.instantiate([BoundedNatArg(k)])

    # xx_phase

    @functools.cached_property
    def xx_phase_def(self) -> OpDef:
        """Apply an XXPhase gate to two qubits within a block.

        This is the generic operation definition. For the instantiated operation, see
        `xx_phase`."""
        return self().get_op("xx_phase")

    def xx_phase(self, k: int, i: int, j: int) -> ExtOp:
        """Apply an XXPhase gate to two qubits within a block.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.xx_phase_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def xx_phase_d_def(self) -> OpDef:
        """Apply an XXPhase gate to two qubits within a block with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `xx_phase_d`."""
        return self().get_op("xx_phase_d")

    def xx_phase_d(self, k: int) -> ExtOp:
        """Apply an XXPhase gate to two qubits within a block with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.xx_phase_d_def.instantiate([BoundedNatArg(k)])

    # yy_phase

    @functools.cached_property
    def yy_phase_def(self) -> OpDef:
        """Apply a YYPhase gate to two qubits within a block.

        This is the generic operation definition. For the instantiated operation, see
        `yy_phase`."""
        return self().get_op("yy_phase")

    def yy_phase(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a YYPhase gate to two qubits within a block.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.yy_phase_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def yy_phase_d_def(self) -> OpDef:
        """Apply a YYPhase gate to two qubits within a block with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `yy_phase_d`."""
        return self().get_op("yy_phase_d")

    def yy_phase_d(self, k: int) -> ExtOp:
        """Apply a YYPhase gate to two qubits within a block with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.yy_phase_d_def.instantiate([BoundedNatArg(k)])

    # zz_phase

    @functools.cached_property
    def zz_phase_def(self) -> OpDef:
        """Apply a ZZPhase gate to two qubits within a block.

        This is the generic operation definition. For the instantiated operation, see
        `zz_phase`."""
        return self().get_op("zz_phase")

    def zz_phase(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a ZZPhase gate to two qubits within a block.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.zz_phase_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def zz_phase_d_def(self) -> OpDef:
        """Apply a ZZPhase gate to two qubits within a block with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `zz_phase_d`."""
        return self().get_op("zz_phase_d")

    def zz_phase_d(self, k: int) -> ExtOp:
        """Apply a ZZPhase gate to two qubits within a block with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.zz_phase_d_def.instantiate([BoundedNatArg(k)])

    # cx

    @functools.cached_property
    def cx_def(self) -> OpDef:
        """Apply a CX gate to two qubits within a block.

        This is the generic operation definition. For the instantiated operation, see
        `cx`."""
        return self().get_op("cx")

    def cx(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a CX gate to two qubits within a block.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.cx_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def cx_d_def(self) -> OpDef:
        """Apply a CX gate to two qubits within a block with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `cx_d`."""
        return self().get_op("cx_d")

    def cx_d(self, k: int) -> ExtOp:
        """Apply a CX gate to two qubits within a block with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.cx_d_def.instantiate([BoundedNatArg(k)])

    # swap

    @functools.cached_property
    def swap_def(self) -> OpDef:
        """Apply a SWAP gate to two qubits within a block.

        This is the generic operation definition. For the instantiated operation, see
        `swap`."""
        return self().get_op("swap")

    def swap(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a SWAP gate to two qubits within a block.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the first logical qubit.
            j: The index of the second logical qubit.
        """
        return self.swap_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def swap_d_def(self) -> OpDef:
        """Apply a SWAP gate to two qubits within a block with dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `swap_d`."""
        return self().get_op("swap_d")

    def swap_d(self, k: int) -> ExtOp:
        """Apply a SWAP gate to two qubits within a block with dynamic indices.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.swap_d_def.instantiate([BoundedNatArg(k)])

    # zz_phase_between_blocks

    @functools.cached_property
    def zz_phase_between_blocks_def(self) -> OpDef:
        """Apply a ZZPhase gate to two qubits on different blocks of the same size.

        This is the generic operation definition. For the instantiated operation, see
        `zz_phase_between_blocks`."""
        return self().get_op("zz_phase_between_blocks")

    def zz_phase_between_blocks(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a ZZPhase gate to two qubits on different blocks of the same size.

        Args:
            k: The number of logical qubits encoded in the blocks.
            i: The index of the logical qubit in the first block.
            j: The index of the logical qubit in the second block.
        """
        return self.zz_phase_between_blocks_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)]
        )

    @functools.cached_property
    def zz_phase_between_blocks_d_def(self) -> OpDef:
        """Apply a ZZPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `zz_phase_between_blocks_d`."""
        return self().get_op("zz_phase_between_blocks_d")

    def zz_phase_between_blocks_d(self, k: int) -> ExtOp:
        """Apply a ZZPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        Args:
            k: The number of logical qubits encoded in the blocks.
        """
        return self.zz_phase_between_blocks_d_def.instantiate([BoundedNatArg(k)])

    # cx_transversal

    @functools.cached_property
    def cx_transversal_def(self) -> OpDef:
        """Apply a CX gate transversally over two blocks of the same size.

        This is the generic operation definition. For the instantiated operation, see
        `cx_transversal`."""
        return self().get_op("cx_transversal")

    def cx_transversal(self, k: int) -> ExtOp:
        """Apply a CX gate transversally over two blocks of the same size.

        Args:
            k: The number of logical qubits encoded in the blocks.
        """
        return self.cx_transversal_def.instantiate([BoundedNatArg(k)])

    # alloc_zero

    @functools.cached_property
    def alloc_zero_def(self) -> OpDef:
        """Allocate a block in the all-zero state.

        This is the generic operation definition. For the instantiated operation, see
        `alloc_zero`."""
        return self().get_op("alloc_zero")

    def alloc_zero(self, k: int) -> ExtOp:
        """Allocate a block in the all-zero state.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.alloc_zero_def.instantiate([BoundedNatArg(k)])

    # free

    @functools.cached_property
    def free_def(self) -> OpDef:
        """Free a block.

        This is the generic operation definition. For the instantiated operation, see
        `free`."""
        return self().get_op("free")

    def free(self, k: int) -> ExtOp:
        """Free a block.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.free_def.instantiate([BoundedNatArg(k)])

    # measure_syndrome

    @functools.cached_property
    def measure_syndrome_def(self) -> OpDef:
        """Perform a syndrome measurement, producing (X,Z) error indicators.

        This is the generic operation definition. For the instantiated operation, see
        `measure_syndrome`."""
        return self().get_op("measure_syndrome")

    def measure_syndrome(self, k: int) -> ExtOp:
        """Perform a syndrome measurement, producing (X,Z) error indicators.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.measure_syndrome_def.instantiate([BoundedNatArg(k)])

    # measure_all

    @functools.cached_property
    def measure_all_def(self) -> OpDef:
        """Destructively measure all qubits in the Z basis.

        This is the generic operation definition. For the instantiated operation, see
        `measure_all`."""
        return self().get_op("measure_all")

    def measure_all(self, k: int) -> ExtOp:
        """Destructively measure all qubits in the Z basis.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.measure_all_def.instantiate([BoundedNatArg(k)])

    # try_measure_one_x

    @functools.cached_property
    def try_measure_one_x_def(self) -> OpDef:
        """Non-destructively measure one qubit in the X basis.

        This operation is fallible and produces a future optional bool.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_x`."""
        return self().get_op("try_measure_one_x")

    def try_measure_one_x(self, k: int, i: int) -> ExtOp:
        """Non-destructively measure one qubit in the X basis.

        This operation is fallible and produces a future optional bool.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.try_measure_one_x_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i)]
        )

    @functools.cached_property
    def try_measure_one_x_d_def(self) -> OpDef:
        """Non-destructively measure one qubit in the X basis with dynamic index.

        This operation is fallible and produces a future optional bool.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_x_d`."""
        return self().get_op("try_measure_one_x_d")

    def try_measure_one_x_d(self, k: int) -> ExtOp:
        """Non-destructively measure one qubit in the X basis with dynamic index.

        This operation is fallible and produces a future optional bool.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.try_measure_one_x_d_def.instantiate([BoundedNatArg(k)])

    # try_measure_one_z

    @functools.cached_property
    def try_measure_one_z_def(self) -> OpDef:
        """Non-destructively measure one qubit in the Z basis.

        This operation is fallible and produces a future optional bool.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_z`."""
        return self().get_op("try_measure_one_z")

    def try_measure_one_z(self, k: int, i: int) -> ExtOp:
        """Non-destructively measure one qubit in the Z basis.

        This operation is fallible and produces a future optional bool.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        return self.try_measure_one_z_def.instantiate(
            [BoundedNatArg(k), BoundedNatArg(i)]
        )

    @functools.cached_property
    def try_measure_one_z_d_def(self) -> OpDef:
        """Non-destructively measure one qubit in the Z basis with dynamic index.

        This operation is fallible and produces a future optional bool.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_z_d`."""
        return self().get_op("try_measure_one_z_d")

    def try_measure_one_z_d(self, k: int) -> ExtOp:
        """Non-destructively measure one qubit in the Z basis with dynamic index.

        This operation is fallible and produces a future optional bool.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.try_measure_one_z_d_def.instantiate([BoundedNatArg(k)])
