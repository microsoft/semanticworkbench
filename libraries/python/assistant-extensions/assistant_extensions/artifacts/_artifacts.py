import contextlib
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable

from assistant_drive import Drive, DriveConfig
from openai import AsyncOpenAI, NotGiven
from openai.types.chat import ChatCompletionMessageParam, ParsedChatCompletion
from openai.types.chat_model import ChatModel
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantCapability,
    AssistantContext,
    ConversationContext,
    storage_directory_for_context,
)

from ._inspector import ArtifactConversationInspectorStateProvider
from ._model import Artifact, ArtifactsConfigModel

logger = logging.getLogger(__name__)

ArtifactsProcessingErrorHandler = Callable[[ConversationContext, str, Exception], Awaitable]


class NoResponseChoicesError(Exception):
    pass


class NoParsedMessageError(Exception):
    pass


# define the structured response format for the AI model
class CreateOrUpdateArtifactsResponseFormat(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The response format for the assistant. Use the assistant_response field for the"
                " response content and the artifacts_to_create_or_update field for any artifacts"
                " to create or update."
            ),
            "required": ["assistant_response", "artifacts_to_create_or_update"],
        }

    assistant_response: str
    artifacts_to_create_or_update: list[Artifact]


@dataclass
class ArtifactsCompletionResponse:
    completion: ParsedChatCompletion[CreateOrUpdateArtifactsResponseFormat]
    assistant_response: str
    artifacts_to_create_or_update: list[Artifact]


async def log_and_send_message_on_error(context: ConversationContext, filename: str, e: Exception) -> None:
    """
    Default error handler for attachment processing, which logs the exception and sends
    a message to the conversation.
    """

    logger.exception("exception occurred processing attachment", exc_info=e)
    await context.send_messages(
        NewConversationMessage(
            content=f"There was an error processing the attachment ({filename}): {e}",
            message_type=MessageType.notice,
            metadata={"attribution": "system"},
        )
    )


class ArtifactsExtension:
    def __init__(
        self,
        assistant: AssistantAppProtocol,
        config_provider: Callable[[AssistantContext], Awaitable[ArtifactsConfigModel]],
        error_handler: ArtifactsProcessingErrorHandler = log_and_send_message_on_error,
    ) -> None:
        """
        ArtifactsExtension manages artifacts for the assistant. Artifacts are files that are
        created during the course of a conversation, such as documents that are generated
        in response to user requests. They become collaborative assets that are shared with
        the user and other participants in the conversation and can be accessed and managed
        through the assistant or the UX.

        Args:
            assistant: The assistant app protocol.
            error_handler: The error handler to use when an error occurs processing an attachment.

        Example:
            ```python
            from assistant_extensions.artifacts import ArtifactsExtension

            assistant = AssistantApp(...)

            artifacts_extension = ArtifactsExtension(assistant)


            # TODO: Add examples of usage here
            ```
        """

        self._error_handler = error_handler

        # add the 'supports_artifacts' capability to the assistant, to indicate that this
        # assistant supports artifacts
        assistant.add_capability(AssistantCapability.supports_artifacts)

        assistant.add_inspector_state_provider(
            "artifacts", ArtifactConversationInspectorStateProvider(config_provider, self)
        )

    def create_or_update_artifact(self, context: ConversationContext, artifact: Artifact) -> None:
        """
        Create or update an artifact with the given filename and contents.
        """
        # check if there is already an artifact with the same filename and version
        existing_artifact = self.get_artifact(context, artifact.filename, artifact.version)
        if existing_artifact:
            # update the existing artifact
            artifact.version = existing_artifact.version + 1
            # try again
            self.create_or_update_artifact(context, artifact)
        else:
            # write the artifact to storage
            drive = _artifact_drive_for_context(context)
            return drive.write_model(artifact, filename=f"artifact.{artifact.version}.json", dir=artifact.filename)

    def get_artifact(
        self, context: ConversationContext, artifact_filename: str, version: int | None = None
    ) -> Artifact | None:
        """
        Read the artifact with the given filename.
        """
        drive = _artifact_drive_for_context(context)
        with contextlib.suppress(FileNotFoundError):
            if version:
                return drive.read_model(Artifact, filename=f"artifact.{version}.json", dir=artifact_filename)
            else:
                return drive.read_model(
                    Artifact,
                    filename=max(
                        drive.list(artifact_filename),
                        key=lambda versioned_filename: int(versioned_filename.split(".")[1]),
                    ),
                    dir=artifact_filename,
                )

    def get_all_artifacts(self, context: ConversationContext) -> list[Artifact]:
        """
        Read all artifacts, will return latest version of each artifact.
        """
        drive = _artifact_drive_for_context(context)
        artifact_filenames = drive.list("")

        artifacts: list[Artifact] = []
        for artifact_filename in artifact_filenames:
            with contextlib.suppress(FileNotFoundError):
                artifact = self.get_artifact(context, artifact_filename)
                if artifact is not None:
                    artifacts.append(artifact)

        return artifacts

    async def delete_artifact(self, context: ConversationContext, artifact_filename: str) -> None:
        """
        Delete the artifact with the given filename.
        """
        drive = _artifact_drive_for_context(context)
        with contextlib.suppress(FileNotFoundError):
            drive.delete(filename=artifact_filename)

    async def get_openai_completion_response(
        self,
        client: AsyncOpenAI,
        messages: Iterable[ChatCompletionMessageParam],
        model: ChatModel | str,
        max_tokens: int | NotGiven | None = None,
    ) -> ArtifactsCompletionResponse:
        """
        Generate a completion response from OpenAI based on the artifacts in the context.
        """

        # call the OpenAI API to generate a completion
        completion = await client.beta.chat.completions.parse(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            response_format=CreateOrUpdateArtifactsResponseFormat,
        )

        if not completion.choices:
            raise NoResponseChoicesError()

        if not completion.choices[0].message.parsed:
            raise NoParsedMessageError()

        return ArtifactsCompletionResponse(
            completion=completion,
            assistant_response=completion.choices[0].message.parsed.assistant_response,
            artifacts_to_create_or_update=completion.choices[0].message.parsed.artifacts_to_create_or_update,
        )


#
# region Helpers
#


def _artifact_drive_for_context(context: ConversationContext, sub_directory: str | None = None) -> Drive:
    """
    Get the Drive instance for the artifacts.
    """
    drive_root = storage_directory_for_context(context) / "artifacts"
    if sub_directory:
        drive_root = drive_root / sub_directory
    return Drive(DriveConfig(root=drive_root))


# endregion
