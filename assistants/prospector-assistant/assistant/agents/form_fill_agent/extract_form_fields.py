from typing import Annotated, Any, Literal

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from .llm_config import LLMConfig


class ExtractFormFieldsConfig(BaseModel):
    instruction: Annotated[
        str, Field(title="Instruction", description="The instruction for extracting form fields from the file content.")
    ] = (
        "Extract the form fields from the provided form attachment. Any type of form is allowed, including for example"
        " tax forms, address forms, surveys, and other official or unofficial form-types. If the content is not a form,"
        " or the fields cannot be determined, then set the error_message."
    )


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
    llm_config: LLMConfig, config: ExtractFormFieldsConfig, form_content: str
) -> tuple[FormFields, dict[str, Any]]:
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": config.instruction,
        },
        {
            "role": "user",
            "content": form_content,
        },
    ]

    async with llm_config.openai_client as client:
        response = await client.beta.chat.completions.parse(
            messages=messages,
            model=llm_config.openai_model,
            response_format=FormFields,
            max_tokens=llm_config.max_response_tokens,
        )

        if not response.choices:
            raise NoResponseChoicesError()

        if not response.choices[0].message.parsed:
            raise NoParsedMessageError()

        metadata = {
            "request": {
                "model": llm_config.openai_model,
                "messages": openai_client.truncate_messages_for_logging(messages),
                "max_tokens": llm_config.max_response_tokens,
                "response_format": FormFields.model_json_schema(),
            },
            "response": response.model_dump(),
        }

        return response.choices[0].message.parsed, metadata
