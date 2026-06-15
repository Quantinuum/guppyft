from dataclasses import dataclass
from typing import ClassVar

from guppylang_internals.diagnostic import Help, Note


@dataclass(frozen=True)
class CallbackUsedHereNote(Note):
    span_label: ClassVar[str] = "Callback function used here."


@dataclass(frozen=True)
class ConsiderOwnedHelper(Help):
    message: ClassVar[str] = "Consider annotating with `@owned`."
