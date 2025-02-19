from typing import Annotated, Literal

from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict, Field


@dataclass
class CompletionMessageImageContent:
    type: Literal["image"]
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
    data: str


@dataclass
class CompletionMessageTextContent:
    type: Literal["text"]
    text: str


@dataclass
class CompletionMessage:
    role: Literal["assistant", "user", "system", "developer"]
    content: str | list[CompletionMessageImageContent | CompletionMessageTextContent]


class RequestConfigBaseModel(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=("The maximum number of tokens to use for both the prompt and response."),
        ),
    ] = 128_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the prompt."
            ),
        ),
    ] = 4_048

    model: Annotated[
        str,
        Field(title="Model", description="The model to use for generating responses."),
    ] = "gpt-4o"
