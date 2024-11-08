import logging
from dataclasses import dataclass
from typing import Annotated, Any

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from .. import state
from . import _llm
from .types import Context, IncompleteErrorResult, IncompleteResult, LLMConfig, Result

logger = logging.getLogger(__name__)


class ExtractFormFieldsConfig(BaseModel):
    instruction: Annotated[
        str,
        Field(title="Instruction", description="The instruction for extracting form fields from the file content."),
        UISchema(widget="textarea"),
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
    file_content: str,
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: extract form fields from the form file content
    Approach: Chat completion with LLM
    """

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
                message=f"Failed to extract form fields: {e}",
                debug={"error": str(e)},
            )

    if extracted_form_fields.error_message:
        return IncompleteResult(
            message=extracted_form_fields.error_message,
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

    return await _llm.structured_completion(
        llm_config=llm_config,
        messages=messages,
        response_model=FormFields,
    )
