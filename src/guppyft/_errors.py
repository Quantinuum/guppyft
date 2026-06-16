import ast
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ClassVar

from guppylang_internals.diagnostic import Error, Help, Note
from guppylang_internals.engine import ENGINE
from guppylang_internals.nodes import GlobalName, PlaceNode
from guppylang_internals.tys.ty import FuncInput, Type


def get_callback_func_ast(callback_expr: ast.expr) -> ast.AST | None:
    match callback_expr:
        case GlobalName():
            return ENGINE.get_parsed(callback_expr.def_id).defined_at
        case PlaceNode():
            return callback_expr.place.defined_at
        case _:
            raise ValueError("Unexpected expression type")


def get_function_input_arg(func_expr: ast.expr, idx: int | None) -> ast.AST | None:
    """Helper function to get ast location of function argument. If `idx` is None, the
    whole function AST is returned."""
    if idx is None:
        return get_callback_func_ast(func_expr)
    else:
        func_args: Sequence[ast.arg] = get_callback_func_ast(func_expr).args.args  # type: ignore[union-attr]
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
class CallbackInputParamError(Error):
    title: ClassVar[str] = "Callback input parameter error"
    span_label: ClassVar[str] = "{kind}"
    callback_def_node: ast.expr
    param_idx: int | None
    kind: str
    span: ast.arg = field(init=False)

    def __post_init__(self) -> None:
        assert isinstance(self.callback_def_node, GlobalName)
        arg = get_function_input_arg(self.callback_def_node, self.param_idx)
        object.__setattr__(self, "span", arg)


@dataclass(frozen=True)
class CallbackOutputArgError(Error):
    title: ClassVar[str] = "Callback function output error."
    span_label: ClassVar[str] = (
        "First return arg must match global type `{expected_str}`."
    )
    expected: Type

    @property
    def expected_str(self) -> str:
        return str(self.expected)


@dataclass(frozen=True)
class CallbackUsedHereNote(Note):
    span_label: ClassVar[str] = "Callback function used here."


@dataclass(frozen=True)
class CallbackFuncDefinedHere(Note):
    span_label: ClassVar[str] = "Callback function defined here."


@dataclass(frozen=True)
class ConsiderOwnedHelper(Help):
    message: ClassVar[str] = "Consider annotating with `@owned`."
