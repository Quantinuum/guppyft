import ast
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ClassVar

from guppylang_internals.definition.common import DefId
from guppylang_internals.diagnostic import Error, Help, Note
from guppylang_internals.engine import ENGINE
from guppylang_internals.nodes import GlobalName
from guppylang_internals.tys.ty import FuncInput, Type


def get_function_input_arg(func_id: DefId, idx: int) -> ast.arg:
    """Helper function to get ast location of function argument"""
    func_args: Sequence[ast.arg] = ENGINE.get_parsed(func_id).defined_at.args.args  # type: ignore[union-attr]
    return func_args[idx]


@dataclass(frozen=True)
class CallbackFuncParametersError(Error):
    title: ClassVar[str] = "Expected callback function parameters ({expected_str})"
    span_label: ClassVar[str] = (
        "Given callback function declared parameters ({expected_str}), but "
        "the provided arguments were ({got_str})"
    )
    expected: Sequence[FuncInput]
    got: Sequence[Type]

    @property
    def expected_str(self) -> str:
        return ", ".join(str(i.ty) for i in self.expected)

    @property
    def got_str(self) -> str:
        return ", ".join(str(i) for i in self.got)


@dataclass(frozen=True)
class BorrowedCallbackParamError(Error):
    title: ClassVar[str] = "Borrowed callback function parameter error."
    span_label: ClassVar[str] = (
        "Parameters in callback functions used in global operation cannot be borrowed."
    )
    callback_def_node: ast.expr
    param_idx: int
    span: ast.arg = field(init=False)

    def __post_init__(self) -> None:
        assert isinstance(self.callback_def_node, GlobalName)
        arg = get_function_input_arg(self.callback_def_node.def_id, self.param_idx)
        object.__setattr__(self, "span", arg)


@dataclass(frozen=True)
class CallbackUsedHereNote(Note):
    span_label: ClassVar[str] = "Callback function used here."


@dataclass(frozen=True)
class CallbackFuncDefinedHere(Note):
    span_label: ClassVar[str] = "Callback function defined here."


@dataclass(frozen=True)
class ConsiderOwnedHelper(Help):
    message: ClassVar[str] = "Consider annotating with `@owned`."
