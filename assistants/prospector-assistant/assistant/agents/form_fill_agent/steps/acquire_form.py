import logging
from dataclasses import dataclass
from pathlib import Path

from guided_conversation.utils.resources import ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import AssistantAppProtocol

from .. import gce_config
from ..inspector import FileStateInspector
from ..step import Context, IncompleteErrorResult, IncompleteResult, Result
from . import gce

logger = logging.getLogger(__name__)


class FormArtifact(BaseModel):
    title: str = Field(description="The title of the form.", default="")
    filename: str = Field(description="The filename of the form.", default="")


definition = gce_config.GuidedConversationDefinition(
    rules=[
        "DO NOT suggest forms or create a form for the user.",
        "Politely request another file if the provided file is not a form.",
        "Terminate conversation if inappropriate content is requested.",
    ],
    conversation_flow=(
        """
        1. Inform the user that our goal is to help the user fill out a form.
        2. Ask the user to provide a file that contains a form. The file can be PDF, TXT, or DOCX.
        3. When you receive a file, determine if the file looks to be a form.
        4. If the file is not a form, inform the user that the file is not a form. Ask them to provide a different file.
        5. If the form is a file, update the artifcat with the title and filename of the form.
        6. Inform the user that you will now extract the form fields, so that you can assist them in filling it out.
        """
    ),
    context="",
    resource_constraint=gce_config.ResourceConstraintDefinition(
        quantity=5,
        unit=ResourceConstraintUnit.MINUTES,
        mode=ResourceConstraintMode.MAXIMUM,
    ),
)


@dataclass
class CompleteResult(Result):
    ai_message: str
    filename: str


async def execute(
    step_context: Context[gce_config.GuidedConversationDefinition],
    latest_user_message: str | None,
) -> IncompleteResult | IncompleteErrorResult | CompleteResult:
    """
    Step: acquire a form from the user
    Approach: Guided conversation
    """
    message_with_attachments = await gce.message_with_recent_attachments(
        step_context.context, latest_user_message, step_context.get_attachment_messages
    )

    async with gce.guided_conversation_with_state(
        definition=step_context.config,
        artifact_type=FormArtifact,
        state_file_path=_get_state_file_path(step_context.context),
        openai_client=step_context.llm_config.openai_client_factory(),
        openai_model=step_context.llm_config.openai_model,
        context=step_context.context,
        state_id=_inspector.state_id,
    ) as guided_conversation:
        try:
            result = await guided_conversation.step_conversation(message_with_attachments)
        except Exception as e:
            logger.exception("failed to execute guided conversation")
            return IncompleteErrorResult(
                error_message=f"Failed to execute guided conversation: {e}",
                debug={"error": str(e)},
            )

        logger.info("guided-conversation result: %s", result)

        acquire_form_gc_artifact = guided_conversation.artifact.artifact.model_dump(mode="json")
        logger.info("guided-conversation artifact: %s", guided_conversation.artifact)

    form_filename = acquire_form_gc_artifact.get("filename", "")

    if form_filename and form_filename != "Unanswered":
        return CompleteResult(
            ai_message=result.ai_message or "",
            filename=form_filename,
            debug={"artifact": acquire_form_gc_artifact},
        )

    return IncompleteResult(
        ai_message=result.ai_message or "",
        debug={"artifact": acquire_form_gc_artifact},
    )


def _get_state_file_path(context: ConversationContext) -> Path:
    return gce.path_for_guided_conversation_state(context, "acquire_form")


_inspector = FileStateInspector(
    display_name="Acquire Form Guided Conversation State",
    file_path_source=_get_state_file_path,
    state_id="acquire_form",
)


def extend(app: AssistantAppProtocol) -> None:
    app.add_inspector_state_provider(_inspector.state_id, _inspector)
