"""
These functions allow you to define a language model prompt in a simple template
language. This makes it simpler to write a prompt in plain text vs assembling a
prompt message by message in code.

Your prompt spec can have any number of `--SYSTEM--`, `--HUMAN--`, or
`--ASSISTANT--` sections representing prompt messages. The messages contain text
that will be used as the content of the messages. You can use variables in any
of these sections by putting the name of variables in curly brackets. The
[../local/llm](invoke_llm) method will replace these with the value of the
variables you pass in.

Example text that can be parsed into a PromptSpec:

--SYSTEM--
The assistant responds to a user like a {personality}.

--USER--
{user_message}

"""

from pathlib import Path
from typing import Any

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class PromptSpec(BaseModel):
    meta: dict[str, str] = Field(description="The meta information of the prompt.")
    messages: list[tuple[str, str]] = Field(description="The dialogue of the prompt.")


def to_chat_completion_messages(template: str | Path, variables: dict[str, Any]) -> list[ChatCompletionMessageParam]:
    if isinstance(template, str):
        prompt_spec = parse_prompt_spec(template)
    else:
        prompt_spec = parse_prompt_file(template)
    messages: list[ChatCompletionMessageParam] = []
    for role, text in prompt_spec.messages:
        formatted_text = text.format(**variables)
        if role == "system":
            messages.append({"role": "system", "content": formatted_text})
        if role == "human":
            messages.append({"role": "user", "content": formatted_text})
        if role == "assistant":
            messages.append({"role": "assistant", "content": formatted_text})
    return messages


def parse_prompt_spec(prompt_spec: str) -> PromptSpec:
    result = PromptSpec(meta={}, messages=[])
    current_section = None
    current_text = []

    def save_section() -> None:
        text = "\n".join(current_text).strip()
        if current_section == "meta":
            meta_values = {}
            for line in text.split("\n"):
                key, value = line.split(":", 1)
                meta_values[key.strip()] = value.strip()
            result.meta = meta_values
        elif current_section == "system":
            result.messages.append(("system", text))
        elif current_section == "human":
            result.messages.append(("human", text))
        elif current_section == "assistant":
            result.messages.append(("assistant", text))

    for line in prompt_spec.split("\n"):
        line = line.strip()
        if line == "--META--":
            save_section()
            current_text = []
            current_section = "meta"
            continue
        elif line == "--SYSTEM--":
            save_section()
            current_text = []
            current_section = "system"
            continue
        elif line in ["--HUMAN--", "--USER--"]:
            save_section()
            current_text = []
            current_section = "human"
            continue
        elif line in ["--ASSISTANT--", "--BOT--"]:
            save_section()
            current_text = []
            current_section = "assistant"
            continue

        if current_section:
            current_text.append(line)

    # Capture the last section
    if current_section and current_text:
        save_section()

    return result


def parse_prompt_file(file_path: Path) -> PromptSpec:
    with open(file_path, "r", encoding="utf-8") as f:
        return parse_prompt_spec(f.read())
