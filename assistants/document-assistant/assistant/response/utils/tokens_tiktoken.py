from collections.abc import Collection
from typing import AbstractSet, Literal

import tiktoken


class TokenizerOpenAI:
    def __init__(
        self,
        model: str,
        allowed_special: Literal["all"] | AbstractSet[str] | None = None,
        disallowed_special: Literal["all"] | Collection[str] | None = None,
    ) -> None:
        self.model = model
        self.allowed_special = allowed_special
        self.disallowed_special = disallowed_special

        self._init_tokenizer(model, allowed_special, disallowed_special)

    def _init_tokenizer(
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

    def truncate_str(self, text: str, max_len: int) -> str:
        tokens = self.encoding.encode(
            text,
            allowed_special=self.allowed_special if self.allowed_special is not None else set(),  # type: ignore
            disallowed_special=self.disallowed_special if self.disallowed_special is not None else (),
        )
        if len(tokens) > max_len:
            tokens = tokens[:max_len]
            truncated_text = self.encoding.decode(tokens)
            return truncated_text
        else:
            return text
