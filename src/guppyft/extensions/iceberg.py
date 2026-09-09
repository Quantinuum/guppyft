"""Iceberg code extension."""

import functools

from hugr.ext import Extension, OpDef, TypeDef
from hugr.ops import ExtOp
from hugr.std.float import FLOAT_T
from hugr.std.int import int_t
from hugr.tys import BoundedNatArg, ExtType, FunctionType, Option
from tket_exts import measurement

from ._util import load_extension

_IDX_T = int_t(6)
_MEAS_T = measurement.measurement_t


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

    @functools.cached_property
    def iceberg_borrowed_block_def(self) -> TypeDef:
        """A borrowed Iceberg code block.

        This is the generic type definition. For the instantiated type, see
        `iceberg_borrowed_block`.
        """
        return self().get_type("borrowed_block")

    def iceberg_borrowed_block(self, k: int) -> ExtType:
        """A borrowed Iceberg code block.

        Args:
            k: The number of logical qubits encoded in the original block.
        """
        return self.iceberg_borrowed_block_def.instantiate([BoundedNatArg(k)])

    @functools.cached_property
    def iceberg_pre_block_def(self) -> TypeDef:
        """An Iceberg code pre-block.

        This is the generic type definition. For the instantiated type, see
        `iceberg_pre_block`.
        """
        return self().get_type("pre_block")

    def iceberg_pre_block(self, k: int) -> ExtType:
        """An Iceberg code pre-block.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        return self.iceberg_pre_block_def.instantiate([BoundedNatArg(k)])

    @functools.cached_property
    def iceberg_qubit_def(self) -> TypeDef:
        """A "dynamic" logical qubit belonging to an unspecified block.

        This is the generic type definition. For the instantiated type, see
        `iceberg_qubit`.
        """
        return self().get_type("qubit")

    def iceberg_qubit(self) -> ExtType:
        """A "dynamic" logical qubit belonging to an unspecified block."""
        return self.iceberg_qubit_def.instantiate([])


_ICEBERG_TYPES = IcebergTypesExtension()
_DYNQ_T = _ICEBERG_TYPES.iceberg_qubit()


class IcebergOpsExtension:
    """Extension providing the Iceberg logical operations."""

    def __call__(self) -> Extension:
        """Returns the Iceberg ops extension"""
        return load_extension("guppyft.iceberg.ops", ["guppyft.std.types"])

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.x_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.x_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

    # y

    @functools.cached_property
    def y_def(self) -> OpDef:
        """Apply a Y gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `y`."""
        return self().get_op("y")

    def y(self, k: int, i: int) -> ExtOp:
        """Apply a Y gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.y_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

    @functools.cached_property
    def y_d_def(self) -> OpDef:
        """Apply a Y gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `y_d`."""
        return self().get_op("y_d")

    def y_d(self, k: int) -> ExtOp:
        """Apply a Y gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.y_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.z_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.z_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_x_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_x_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_z_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_z_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_x_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_y_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_z_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.x_with_all_but_one_z_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.x_with_all_but_one_z_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.z_with_all_but_one_x_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.z_with_all_but_one_x_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.fan_out_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.fan_out_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.fan_in_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.fan_in_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.rx_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.rx_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, FLOAT_T], [block_type]
            ),
        )

    # ry

    @functools.cached_property
    def ry_def(self) -> OpDef:
        """Apply an Ry gate to one qubit.

        This is the generic operation definition. For the instantiated operation, see
        `ry`."""
        return self().get_op("ry")

    def ry(self, k: int, i: int) -> ExtOp:
        """Apply an Ry gate to one qubit.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.ry_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

    @functools.cached_property
    def ry_d_def(self) -> OpDef:
        """Apply an Ry gate to one qubit with dynamic index.

        This is the generic operation definition. For the instantiated operation, see
        `ry_d`."""
        return self().get_op("ry_d")

    def ry_d(self, k: int) -> ExtOp:
        """Apply an Ry gate to one qubit with dynamic index.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.ry_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.rz_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.rz_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_rx_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_ry_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_rz_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_rx_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_rx_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_rz_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_but_one_rz_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.all_h_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_phase_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_phase_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_phase_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_phase_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_phase_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type, FLOAT_T], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_phase_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T, _IDX_T, FLOAT_T], [block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.cx_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.cx_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T, _IDX_T], [block_type]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.swap_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType([block_type], [block_type]),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.swap_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type, _IDX_T, _IDX_T], [block_type]),
        )

    # xx_phase_between_blocks

    @functools.cached_property
    def xx_phase_between_blocks_def(self) -> OpDef:
        """Apply an XXPhase gate to two qubits on different blocks of the same size.

        This is the generic operation definition. For the instantiated operation, see
        `xx_phase_between_blocks`."""
        return self().get_op("xx_phase_between_blocks")

    def xx_phase_between_blocks(self, k: int, i: int, j: int) -> ExtOp:
        """Apply an XXPhase gate to two qubits on different blocks of the same size.

        Args:
            k: The number of logical qubits encoded in the blocks.
            i: The index of the logical qubit in the first block.
            j: The index of the logical qubit in the second block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_phase_between_blocks_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType(
                [block_type, block_type, FLOAT_T], [block_type, block_type]
            ),
        )

    @functools.cached_property
    def xx_phase_between_blocks_d_def(self) -> OpDef:
        """Apply an XXPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `xx_phase_between_blocks_d`."""
        return self().get_op("xx_phase_between_blocks_d")

    def xx_phase_between_blocks_d(self, k: int) -> ExtOp:
        """Apply an XXPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        Args:
            k: The number of logical qubits encoded in the blocks.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.xx_phase_between_blocks_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, block_type, _IDX_T, _IDX_T, FLOAT_T],
                [block_type, block_type],
            ),
        )

    # yy_phase_between_blocks

    @functools.cached_property
    def yy_phase_between_blocks_def(self) -> OpDef:
        """Apply a YYPhase gate to two qubits on different blocks of the same size.

        This is the generic operation definition. For the instantiated operation, see
        `yy_phase_between_blocks`."""
        return self().get_op("yy_phase_between_blocks")

    def yy_phase_between_blocks(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a YYPhase gate to two qubits on different blocks of the same size.

        Args:
            k: The number of logical qubits encoded in the blocks.
            i: The index of the logical qubit in the first block.
            j: The index of the logical qubit in the second block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_phase_between_blocks_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType(
                [block_type, block_type, FLOAT_T], [block_type, block_type]
            ),
        )

    @functools.cached_property
    def yy_phase_between_blocks_d_def(self) -> OpDef:
        """Apply a YYPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `yy_phase_between_blocks_d`."""
        return self().get_op("yy_phase_between_blocks_d")

    def yy_phase_between_blocks_d(self, k: int) -> ExtOp:
        """Apply a YYPhase gate to two qubits on different blocks of the same size with
        dynamic indices.

        Args:
            k: The number of logical qubits encoded in the blocks.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.yy_phase_between_blocks_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, block_type, _IDX_T, _IDX_T, FLOAT_T],
                [block_type, block_type],
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_phase_between_blocks_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType(
                [block_type, block_type, FLOAT_T], [block_type, block_type]
            ),
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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.zz_phase_between_blocks_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, block_type, _IDX_T, _IDX_T, FLOAT_T],
                [block_type, block_type],
            ),
        )

    # cx_between_blocks

    @functools.cached_property
    def cx_between_blocks_def(self) -> OpDef:
        """Apply a CX gate to two qubits on different blocks of the same size.

        This is the generic operation definition. For the instantiated operation, see
        `cx_between_blocks`."""
        return self().get_op("cx_between_blocks")

    def cx_between_blocks(self, k: int, i: int, j: int) -> ExtOp:
        """Apply a CX gate to two qubits on different blocks of the same size.

        Args:
            k: The number of logical qubits encoded in the blocks.
            i: The index of the logical qubit in the first block.
            j: The index of the logical qubit in the second block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.cx_between_blocks_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i), BoundedNatArg(j)],
            concrete_signature=FunctionType(
                [block_type, block_type], [block_type, block_type]
            ),
        )

    @functools.cached_property
    def cx_between_blocks_d_def(self) -> OpDef:
        """Apply a CX gate to two qubits on different blocks of the same size with
        dynamic indices.

        This is the generic operation definition. For the instantiated operation, see
        `cx_between_blocks_d`."""
        return self().get_op("cx_between_blocks_d")

    def cx_between_blocks_d(self, k: int) -> ExtOp:
        """Apply a CX gate to two qubits on different blocks of the same size with
        dynamic indices.

        Args:
            k: The number of logical qubits encoded in the blocks.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.cx_between_blocks_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, block_type, _IDX_T, _IDX_T], [block_type, block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.cx_transversal_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, block_type], [block_type, block_type]
            ),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.alloc_zero_def.instantiate(
            args=[BoundedNatArg(k)], concrete_signature=FunctionType([], [block_type])
        )

    # try_alloc_zero

    @functools.cached_property
    def try_alloc_zero_def(self) -> OpDef:
        """Allocate a `PreBlock` in the all-zero state.

        This is the generic operation definition. For the instantiated operation, see
        `alloc_zero`."""
        return self().get_op("try_alloc_zero")

    def try_alloc_zero(self, k: int) -> ExtOp:
        """Allocate a `PreBlock` in the all-zero state.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        preblock_type = _ICEBERG_TYPES.iceberg_pre_block(k)
        return self.try_alloc_zero_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([], [preblock_type]),
        )

    # check_pre_block

    @functools.cached_property
    def check_pre_block_def(self) -> OpDef:
        """Check if a `PreBlock` is in a valid logical state.

        This is the generic operation definition. For the instantiated operation, see
        `check`."""
        return self().get_op("check_pre_block")

    def check_pre_block(self, k: int) -> ExtOp:
        """Check if a `PreBlock` is in a valid logical state.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        preblock_type = _ICEBERG_TYPES.iceberg_pre_block(k)
        return self.check_pre_block_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([preblock_type], [Option(block_type)]),
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.free_def.instantiate(
            args=[BoundedNatArg(k)], concrete_signature=FunctionType([block_type], [])
        )

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
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.measure_syndrome_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type], [block_type, _MEAS_T, _MEAS_T]
            ),
        )

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
        from guppyft.extensions import std_types

        block_type = _ICEBERG_TYPES.iceberg_block(k)
        lmeas_type = std_types.logical_measurement(k)
        return self.measure_all_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType([block_type], [lmeas_type]),
        )

    # try_measure_one_x

    @functools.cached_property
    def try_measure_one_x_def(self) -> OpDef:
        """Non-destructively measure one qubit in the X basis.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_x`."""
        return self().get_op("try_measure_one_x")

    def try_measure_one_x(self, k: int, i: int) -> ExtOp:
        """Non-destructively measure one qubit in the X basis.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.try_measure_one_x_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType(
                [block_type], [Option(_MEAS_T), block_type]
            ),
        )

    @functools.cached_property
    def try_measure_one_x_d_def(self) -> OpDef:
        """Non-destructively measure one qubit in the X basis with dynamic index.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_x_d`."""
        return self().get_op("try_measure_one_x_d")

    def try_measure_one_x_d(self, k: int) -> ExtOp:
        """Non-destructively measure one qubit in the X basis with dynamic index.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.try_measure_one_x_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T], [Option(_MEAS_T), block_type]
            ),
        )

    # try_measure_one_z

    @functools.cached_property
    def try_measure_one_z_def(self) -> OpDef:
        """Non-destructively measure one qubit in the Z basis.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_z`."""
        return self().get_op("try_measure_one_z")

    def try_measure_one_z(self, k: int, i: int) -> ExtOp:
        """Non-destructively measure one qubit in the Z basis.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        Args:
            k: The number of logical qubits encoded in the block.
            i: The index of the logical qubit.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.try_measure_one_z_def.instantiate(
            args=[BoundedNatArg(k), BoundedNatArg(i)],
            concrete_signature=FunctionType(
                [block_type], [Option(_MEAS_T), block_type]
            ),
        )

    @functools.cached_property
    def try_measure_one_z_d_def(self) -> OpDef:
        """Non-destructively measure one qubit in the Z basis with dynamic index.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        This is the generic operation definition. For the instantiated operation, see
        `try_measure_one_z_d`."""
        return self().get_op("try_measure_one_z_d")

    def try_measure_one_z_d(self, k: int) -> ExtOp:
        """Non-destructively measure one qubit in the Z basis with dynamic index.

        This operation is fallible and produces a future optional bool. A "none"
        value indicates a probable single-qubit error; QED may then be used to
        detect whether this was just a measurement error or whether it affected
        the data qubits.

        Args:
            k: The number of logical qubits encoded in the block.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        return self.try_measure_one_z_d_def.instantiate(
            args=[BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type, _IDX_T], [Option(_MEAS_T), block_type]
            ),
        )

    # alloc_dynq

    @functools.cached_property
    def alloc_dynq(self) -> OpDef:
        """Allocate a dynamic logical qubit in the zero state."""
        return self().get_op("alloc_dynq")

    # try_alloc_dynq

    @functools.cached_property
    def try_alloc_dynq(self) -> OpDef:
        """Try to allocate a dynamic logical qubit in the zero state."""
        return self().get_op("try_alloc_dynq")

    # free_dynq

    @functools.cached_property
    def free_dynq(self) -> OpDef:
        """Discard a dynamic logical qubit."""
        return self().get_op("free_dynq")

    # x_dynq

    @functools.cached_property
    def x_dynq(self) -> OpDef:
        """X gate on a dynamic logical qubit."""
        return self().get_op("x_dynq")

    # y_dynq

    @functools.cached_property
    def y_dynq(self) -> OpDef:
        """Y gate on a dynamic logical qubit."""
        return self().get_op("y_dynq")

    # z_dynq

    @functools.cached_property
    def z_dynq(self) -> OpDef:
        """Z gate on a dynamic logical qubit."""
        return self().get_op("z_dynq")

    # rx_dynq

    @functools.cached_property
    def rx_dynq(self) -> OpDef:
        """Rx gate on a dynamic logical qubit."""
        return self().get_op("rx_dynq")

    # ry_dynq

    @functools.cached_property
    def ry_dynq(self) -> OpDef:
        """Ry gate on a dynamic logical qubit."""
        return self().get_op("ry_dynq")

    # rz_dynq

    @functools.cached_property
    def rz_dynq(self) -> OpDef:
        """Rz gate on a dynamic logical qubit."""
        return self().get_op("rz_dynq")

    # xx_phase_dynq

    @functools.cached_property
    def xx_phase_dynq(self) -> OpDef:
        """XXPhase gate on two dynamic logical qubits."""
        return self().get_op("xx_phase_dynq")

    # yy_phase_dynq

    @functools.cached_property
    def yy_phase_dynq(self) -> OpDef:
        """YYPhase gate on two dynamic logical qubits."""
        return self().get_op("yy_phase_dynq")

    # zz_phase_dynq

    @functools.cached_property
    def zz_phase_dynq(self) -> OpDef:
        """ZZPhase gate on two dynamic logical qubits."""
        return self().get_op("zz_phase_dynq")

    # cx_dynq

    @functools.cached_property
    def cx_dynq(self) -> OpDef:
        """CX gate on two dynamic logical qubits.."""
        return self().get_op("cx_dynq")

    # try_measure_x_dynq

    @functools.cached_property
    def try_measure_x_dynq(self) -> OpDef:
        """Fallible non-destructive measurement of a dynamic logical qubit in the X
        basis."""
        return self().get_op("try_measure_x_dynq")

    # try_measure_z_dynq

    @functools.cached_property
    def try_measure_z_dynq(self) -> OpDef:
        """Fallible non-destructive measurement of a dynamic logical qubit in the Z
        basis."""
        return self().get_op("try_measure_z_dynq")

    # borrow

    @functools.cached_property
    def borrow_def(self) -> OpDef:
        """Extraction of dynamic logical qubits from a block.

        This is the generic operation definition. For the instantiated operation, see
        `borrow`."""
        return self().get_op("borrow")

    def borrow(self, k: int, m: int) -> ExtOp:
        """Extraction of dynamic logical qubits from a block.

        Args:
            k: The number of logical qubits encoded in the block.
            m: The number of logical qubits to borrow.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        bblock_type = _ICEBERG_TYPES.iceberg_borrowed_block(k)
        return self.borrow_def.instantiate(
            args=[BoundedNatArg(m), BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [block_type] + [_IDX_T] * m,  # type: ignore[arg-type]
                [bblock_type] + [_DYNQ_T] * m,  # type: ignore[arg-type]
            ),
        )

    # borrow_more

    @functools.cached_property
    def borrow_more_def(self) -> OpDef:
        """Extraction of dynamic logical qubits from an already-borrowed block.

        This is the generic operation definition. For the instantiated operation, see
        `borrow_more`."""
        return self().get_op("borrow_more")

    def borrow_more(self, k: int, m: int) -> ExtOp:
        """Extraction of dynamic logical qubits from an already-borrowed block.

        Args:
            k: The number of logical qubits encoded in the block.
            m: The number of logical qubits to borrow.
        """
        bblock_type = _ICEBERG_TYPES.iceberg_borrowed_block(k)
        return self.borrow_more_def.instantiate(
            args=[BoundedNatArg(m), BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [bblock_type] + [_IDX_T] * m,  # type: ignore[arg-type]
                [bblock_type] + [_DYNQ_T] * m,  # type: ignore[arg-type]
            ),
        )

    # restore_some

    @functools.cached_property
    def restore_some_def(self) -> OpDef:
        """Restoration of some dynamic logical qubits to their originating block.

        This is the generic operation definition. For the instantiated operation, see
        `restore_some`."""
        return self().get_op("restore_some")

    def restore_some(self, k: int, m: int) -> ExtOp:
        """Restoration of some dynamic logical qubits to their originating block.

        Args:
            k: The number of logical qubits encoded in the block.
            m: The number of logical qubits to restore.
        """
        bblock_type = _ICEBERG_TYPES.iceberg_borrowed_block(k)
        return self.restore_some_def.instantiate(
            args=[BoundedNatArg(m), BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [bblock_type] + [_DYNQ_T] * m,  # type: ignore[arg-type]
                [bblock_type],
            ),
        )

    # restore

    @functools.cached_property
    def restore_def(self) -> OpDef:
        """Restoration of all dynamic logical qubits to their originating block.

        This is the generic operation definition. For the instantiated operation, see
        `restore`."""
        return self().get_op("restore")

    def restore(self, k: int, m: int) -> ExtOp:
        """Restoration of all dynamic logical qubits to their originating block.

        Args:
            k: The number of logical qubits encoded in the block.
            m: The number of logical qubits to restore.
        """
        block_type = _ICEBERG_TYPES.iceberg_block(k)
        bblock_type = _ICEBERG_TYPES.iceberg_borrowed_block(k)
        return self.restore_def.instantiate(
            args=[BoundedNatArg(m), BoundedNatArg(k)],
            concrete_signature=FunctionType(
                [bblock_type] + [_DYNQ_T] * m,  # type: ignore[arg-type]
                [block_type],
            ),
        )
