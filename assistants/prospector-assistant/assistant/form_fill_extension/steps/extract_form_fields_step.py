import logging
from dataclasses import dataclass
from typing import Annotated, Any

from openai.types.chat import ChatCompletionContentPartImageParam, ChatCompletionMessageParam
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from .. import state
from . import _llm
from .types import Context, IncompleteErrorResult, IncompleteResult, LLMConfig, Result, UserAttachment

logger = logging.getLogger(__name__)


class ExtractFormFieldsConfig(BaseModel):
    instruction: Annotated[
        str,
        Field(title="Instruction", description="The instruction for extracting form fields from the file content."),
        UISchema(widget="textarea"),
    ] = (
        "The user has provided a file that might be a form document. {text_or_image}. Determine if the provided file is a form."
        " Determine what sections and fields are in the user provided document. Any type of form is allowed, including tax forms,"
        " address forms, surveys, and other official or unofficial form-types. The goal is to analyze the user provided form, and"
        " report what you find. Do not make up a form or populate the form details with a random form. If the user provided document"
        " is not a form, or the fields cannot be determined, then explain the reason why in the error_message. If the fields can be"
        " determined, leave the error_message empty."
    )


@dataclass
class CompleteResult(Result):
    message: str
    extracted_form: state.Form


async def execute(
    step_context: Context[ExtractFormFieldsConfig],
    potential_form_attachment: UserAttachment,
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: extract form fields from the form file content
    Approach: Chat completion with LLM
    """

    async with step_context.context.set_status("inspecting file ..."):
        try:
            extracted_form_fields, metadata = await _extract(
                llm_config=step_context.llm_config,
                config=step_context.config,
                potential_form_attachment=potential_form_attachment,
            )

        except Exception as e:
            logger.exception("failed to extract form fields")
            return IncompleteErrorResult(
                message=f"Failed to extract form fields: {e}",
                debug={"error": str(e)},
            )

    if not extracted_form_fields.form:
        return IncompleteResult(
            message=extracted_form_fields.error_message,
            debug=metadata,
        )

    return CompleteResult(
        message="The form fields have been extracted.",
        extracted_form=extracted_form_fields.form,
        debug=metadata,
    )


class FormDetails(BaseModel):
    error_message: str = Field(
        description="The error message in the case that the form fields could not be determined."
    )
    form: state.Form | None = Field(
        description="The form and it's details, if they can be determined from the user provided file."
    )


async def _extract(
    llm_config: LLMConfig, config: ExtractFormFieldsConfig, potential_form_attachment: UserAttachment
) -> tuple[FormDetails, dict[str, Any]]:
    match potential_form_attachment.filename.split(".")[-1].lower():
        case "png":
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": config.instruction.replace(
                        "{text_or_image}", "The provided message is a screenshot of the potential form."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        ChatCompletionContentPartImageParam(
                            image_url={
                                "url": potential_form_attachment.content,
                            },
                            type="image_url",
                        )
                    ],
                },
            ]

        case _:
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": config.instruction.replace(
                        "{text_or_image}", "The form has been provided as a text document."
                    ),
                },
                {
                    "role": "user",
                    "content": potential_form_attachment.content,
                },
            ]

    return await _llm.structured_completion(
        llm_config=llm_config,
        messages=messages,
        response_model=FormDetails,
    )
