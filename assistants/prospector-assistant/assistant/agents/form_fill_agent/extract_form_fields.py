from typing import Any, Literal

import openai_client
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class FormField(BaseModel):
    id: str = Field(description="The unique identifier of the field.")
    name: str = Field(description="The name of the field.")
    description: str = Field(description="The description of the field.")
    type: Literal["string", "bool", "multiple_choice"] = Field(description="The type of the field.")
    options: list[str] = Field(description="The options for multiple choice fields.")
    required: bool = Field(description="Whether the field is required or not.")


class FormFields(BaseModel):
    error_message: str = Field(description="The error message in the case that the form fields could not be extracted.")
    fields: list[FormField] = Field(description="The fields in the form.")


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


async def extract(
    async_openai_client: AsyncOpenAI, openai_model: str, max_response_tokens: int, form_content: str
) -> tuple[FormFields, dict[str, Any]]:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                "Extract the form fields from the provided form attachment. Any type of form is allowed, including for example"
                " tax forms, address forms, surveys, and other official or unofficial form-types. If the content is not a form,"
                " or the fields cannot be determined, then set the error_message."
            ),
        },
        {
            "role": "user",
            "content": form_content,
        },
    ]

    async with async_openai_client as client:
        response = await client.beta.chat.completions.parse(
            messages=messages,
            model=openai_model,
            response_format=FormFields,
        )

        if not response.choices:
            raise NoResponseChoicesError()

        if not response.choices[0].message.parsed:
            raise NoParsedMessageError()

        metadata = {
            "request": {
                "model": openai_model,
                "messages": openai_client.truncate_messages_for_logging(messages),
                "max_tokens": max_response_tokens,
                "response_format": FormFields.model_json_schema(),
            },
            "response": response.model_dump(),
        }

        return response.choices[0].message.parsed, metadata
