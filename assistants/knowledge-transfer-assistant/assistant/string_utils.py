from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List

from liquid import Template
from openai.types.chat import ChatCompletionMessageParam


def render(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    parsed = template
    if not vars:
        return template
    liquid_template = Template(template)
    parsed = liquid_template.render(**vars)
    return parsed


def create_system_message(
    content: str, delimiter: str | None = None
) -> ChatCompletionMessageParam:
    if delimiter:
        content = f"<{delimiter}>\n{content}\n</{delimiter}>"

    message: ChatCompletionMessageParam = {
        "role": "system",
        "content": content,
    }
    return message


class Instructions:
    """
    A class to represent a section of a prompt.
    """

    def __init__(
        self,
        content: str,
        title: str | None = None,
    ) -> None:
        self.title = title
        self.content = content
        self.level = 0
        self.subsections: list[Instructions] = []

    def add_subsection(self, subsection: "Instructions") -> None:
        """
        Add a subsection to the prompt section.
        """
        subsection.level = self.level + 1
        self.subsections.append(subsection)

    def __str__(self) -> str:
        s = ""
        if self.title:
            hashes = "#" * (self.level + 1)
            s += f"{hashes} {self.title}\n\n"
        s += self.content
        if self.subsections:
            s += "\n\n" + "\n\n".join(
                str(subsection) for subsection in self.subsections
            )

        return s


class Context:
    def __init__(self, name: str, data: str, description: str | None = None) -> None:
        self.name = name
        self.description = description
        self.data = data

    def message(self) -> ChatCompletionMessageParam:
        return create_system_message(self.content(), self.name)

    def content(self) -> str:
        s = self.data
        if self.description:
            s = f"{self.description}\n\n'''\n{self.data}\n'''"
        return s


class ContextStrategy(Enum):
    SINGLE = "single"  # Put all contexts in a single message.
    MULTI = "multi"  # Put each context in its own message.


@dataclass
class Prompt:
    role: str
    instructions: Instructions
    output_format: str | None = None
    reasoning_steps: str | None = None
    examples: str | None = None
    contexts: List[Context] = field(default_factory=list)
    context_strategy: ContextStrategy = ContextStrategy.SINGLE
    final_instructions: str | None = None

    def messages(self) -> list[ChatCompletionMessageParam]:
        parts = [
            "# Role and Objective",
            self.role,
            "# Instructions",
            str(self.instructions),
        ]
        if self.reasoning_steps:
            parts.append("# Reasoning Steps")
            parts.append(self.reasoning_steps)
        if self.output_format:
            parts.append("# Output Format")
            parts.append(self.output_format)
        if self.examples:
            parts.append("# Examples")
            parts.append(self.examples)
        if self.contexts and self.context_strategy == ContextStrategy.SINGLE:
            parts.append("# Context")
            for context in self.contexts:
                parts.append(f"## {context.name}")
                parts.append(context.content())
        s = "\n\n".join(parts)
        if self.final_instructions:
            s += "\n\n" + self.final_instructions

        messages = [
            create_system_message(s),
        ]

        if self.contexts and self.context_strategy == ContextStrategy.MULTI:
            for context in self.contexts:
                messages.append(context.message())

        return messages


class TokenBudget:
    def __init__(self, budget: int) -> None:
        self.budget = budget
        self.used = 0

    def add(self, tokens: int) -> None:
        self.used += tokens

    def remaining(self) -> int:
        return self.budget - self.used

    def is_under_budget(self) -> bool:
        return self.remaining() > 0

    def is_over_budget(self) -> bool:
        return self.remaining() < 0

    def fits(self, tokens: int) -> bool:
        return self.remaining() >= tokens
