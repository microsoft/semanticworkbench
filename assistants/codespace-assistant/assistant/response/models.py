from typing import Any, Literal

from attr import dataclass


@dataclass
class StepResult:
    status: Literal["final", "error", "continue"]
    conversation_tokens: int = 0
    metadata: dict[str, Any] | None = None
