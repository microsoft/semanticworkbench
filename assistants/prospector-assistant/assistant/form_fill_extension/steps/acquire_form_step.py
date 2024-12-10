import logging
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from ..inspector import FileStateInspector
from . import _guided_conversation
from .types import (
    Context,
    GuidedConversationDefinition,
    IncompleteErrorResult,
    IncompleteResult,
    ResourceConstraintDefinition,
    Result,
    UserInput,
)

logger = logging.getLogger(__name__)


def extend(app: AssistantAppProtocol) -> None:
    app.add_inspector_state_provider(_inspector.state_id, _inspector)


class FormArtifact(BaseModel):
    filename: str = Field(description="The filename of the form.", default="")


definition = GuidedConversationDefinition(
    rules=[
        "DO NOT suggest forms or create a form for the user.",
        "Politely request another file if the provided file is not a form.",
        "Terminate conversation if inappropriate content is requested.",
    ],
    conversation_flow=dedent("""
        1. Inform the user that our goal is to help the user fill out a form.
        2. Ask the user to provide a file that contains a form. The file can be PDF, TXT, DOCX, or PNG.
        3. When you receive a file, set the filename field in the artifact.
        4. Inform the user that you will now extract the form fields, so that you can assist them in filling it out.
    """).strip(),
    context="",
    resource_constraint=ResourceConstraintDefinition(
        quantity=5,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)


class AcquireFormConfig(BaseModel):
    definition: GuidedConversationDefinition = definition


@dataclass
class CompleteResult(Result):
    message: str
    filename: str


async def execute(
    step_context: Context[AcquireFormConfig],
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: acquire a form from the user
    Approach: Guided conversation
    """
    message_with_attachments = await input_to_message(step_context.latest_user_input)

    async with _guided_conversation.engine(
        definition=step_context.config.definition,
        artifact_type=FormArtifact,
        state_file_path=_get_state_file_path(step_context.context),
        openai_client=step_context.llm_config.openai_client_factory(),
        openai_model=step_context.llm_config.openai_model,
        context=step_context.context,
        state_id=_inspector.state_id,
    ) as gce:
        try:
            result = await gce.step_conversation(message_with_attachments)
        except Exception as e:
            logger.exception("failed to execute guided conversation")
            return IncompleteErrorResult(
                message=f"Failed to execute guided conversation: {e}",
                debug={"error": str(e)},
            )

        debug = {"guided-conversation": gce.to_json()}

        logger.info("guided-conversation result: %s", result)

        acquire_form_gc_artifact = gce.artifact.artifact.model_dump(mode="json")
        logger.info("guided-conversation artifact: %s", gce.artifact)

    form_filename = acquire_form_gc_artifact.get("filename", "")

    if form_filename and form_filename != "Unanswered":
        return CompleteResult(
            message=result.ai_message or "",
            filename=form_filename,
            debug=debug,
        )

    return IncompleteResult(message=result.ai_message or "", debug=debug)


def _get_state_file_path(context: ConversationContext) -> Path:
    return _guided_conversation.path_for_state(context, "acquire_form")


_inspector = FileStateInspector(
    display_name="Debug: Acquire-Form Guided-Conversation",
    file_path_source=_get_state_file_path,
)


async def input_to_message(input: UserInput) -> str | None:
    attachments = []
    async for attachment in input.attachments:
        attachments.append(f"<ATTACHMENT>{attachment.filename}</ATTACHMENT>")

    if not attachments:
        return input.message

    return "\n\n".join(
        (
            input.message or "",
            *attachments,
        ),
    )
