import logging
from dataclasses import dataclass
from typing import Annotated, Any

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from .. import state
from . import _attachments
from .types import Context, IncompleteErrorResult, IncompleteResult, LLMConfig, Result

logger = logging.getLogger(__name__)


class ExtractFormFieldsConfig(BaseModel):
    instruction: Annotated[
        str, Field(title="Instruction", description="The instruction for extracting form fields from the file content.")
    ] = (
        "Extract the form fields from the provided form attachment. Any type of form is allowed, including for example"
        " tax forms, address forms, surveys, and other official or unofficial form-types. If the content is not a form,"
        " or the fields cannot be determined, then set the error_message."
    )


@dataclass
class CompleteResult(Result):
    ai_message: str
    extracted_form_fields: list[state.FormField]


async def execute(
    step_context: Context[ExtractFormFieldsConfig],
    filename: str,
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: extract form fields from the form file content
    Approach: Chat completion with LLM
    """

    file_content = await _attachments.attachment_for_filename(filename, step_context.get_attachment_messages)
    async with step_context.context.set_status("inspecting form ..."):
        try:
            extracted_form_fields, metadata = await _extract(
                llm_config=step_context.llm_config,
                config=step_context.config,
                form_content=file_content,
            )

        except Exception as e:
            logger.exception("failed to extract form fields")
            return IncompleteErrorResult(
                error_message=f"Failed to extract form fields: {e}",
                debug={"error": str(e)},
            )

    if extracted_form_fields.error_message:
        return IncompleteResult(
            ai_message=extracted_form_fields.error_message,
            debug=metadata,
        )

    return CompleteResult(
        ai_message="",
        extracted_form_fields=extracted_form_fields.fields,
        debug=metadata,
    )


class FormFields(BaseModel):
    error_message: str = Field(description="The error message in the case that the form fields could not be extracted.")
    fields: list[state.FormField] = Field(description="The fields in the form.")


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


async def _extract(
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

    async with llm_config.openai_client_factory() as client:
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
