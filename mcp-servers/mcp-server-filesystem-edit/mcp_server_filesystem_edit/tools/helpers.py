# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Collection
from typing import AbstractSet, Literal

import tiktoken
from mcp_extensions.llm.llm_types import MessageT


def format_chat_history(chat_history: list[MessageT]) -> str:
    formatted_chat_history = ""
    for message in chat_history:
        formatted_chat_history += f"[{message.role.value}]: {message.content}\n"
    return formatted_chat_history.strip()


class TokenizerOpenAI:
    def __init__(
        self,
        model: str,
        allowed_special: Literal["all"] | AbstractSet[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ):
        self.model = model
        self.allowed_special = allowed_special
        self.disallowed_special = disallowed_special

        self.init_tokenizer(model, allowed_special, disallowed_special)

    def init_tokenizer(
        self,
        model: str,
        allowed_special: Literal["all"] | AbstractSet[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ) -> None:
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            default_encoding = "o200k_base"
            self.encoding = tiktoken.get_encoding(default_encoding)

        # Set defaults if not provided
        if not allowed_special:
            self.allowed_special = set()
        if not disallowed_special:
            self.disallowed_special = ()

    def num_tokens_in_str(self, text: str) -> int:
        return len(
            self.encoding.encode(
                text,
                allowed_special=self.allowed_special if self.allowed_special is not None else set(),  # type: ignore
                disallowed_special=self.disallowed_special if self.disallowed_special is not None else (),
            )
        )
