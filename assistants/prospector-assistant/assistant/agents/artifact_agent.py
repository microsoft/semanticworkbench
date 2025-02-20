from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Union

from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    BaseModelAssistantConfig,
    ConversationContext,
    storage_directory_for_context,
)
from semantic_workbench_assistant.config import UISchema
from semantic_workbench_assistant.storage import read_model, write_model

from .. import helpers

if TYPE_CHECKING:
    from ..config import AssistantConfigModel

#
# region Models
#


class ArtifactAgentConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description=helpers.load_text_include("artifact_agent_enabled.md"),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = False

    instruction_prompt: Annotated[
        str,
        Field(
            description="The prompt to provide instructions for creating or updating an artifact.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are able to create artifacts that will be shared with the others in this conversation."
        " Please include any desired new artifacts or updates to existing artifacts. If this is an"
        " intentional variant to explore another idea, create a new artifact to reflect that. Do not"
        " include the artifacts in the assistant response, as any included artifacts will be shown"
        " to the other conversation participant(s) in a well-formed presentation. Do not include any"
        " commentary or instructions in the artifacts, as they will be presented as-is. If you need"
        " to provide context or instructions, use the conversation text. Each artifact should have be"
        " complete and self-contained. If you are editing an existing artifact, please provide the"
        " full updated content (not just the updated fragments) and a new version number."
    )

    context_description: Annotated[
        str,
        Field(
            description="The description of the context for general response generation.",
        ),
        UISchema(widget="textarea"),
    ] = "These artifacts were developed collaboratively during the conversation."

    include_in_response_generation: Annotated[
        bool,
        Field(
            description=(
                "Whether to include the contents of artifacts in the context for general response generation."
            ),
        ),
    ] = True


class ArtifactMarkdownContent(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The content of the artifact in markdown format. Use this type for any general text that"
                " does not match another, more specific type."
            ),
            "required": ["content_type"],
        }

    content_type: Literal["markdown"] = "markdown"


class ArtifactCodeContent(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The content of the artifact in code format with a specified language for syntax highlighting."
            ),
            "required": ["content_type", "language"],
        }

    content_type: Literal["code"] = "code"
    language: str


class ArtifactMermaidContent(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": "The content of the artifact in mermaid format, which will be rendered as a diagram.",
            "required": ["content_type"],
        }

    content_type: Literal["mermaid"] = "mermaid"


class ArtifactAbcContent(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "The content of the artifact in abc format, which will be rendered as sheet music, an interactive player,"
                " and available for download."
            ),
            "required": ["content_type"],
        }

    content_type: Literal["abc"] = "abc"


class ArtifactExcalidrawContent(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": ("The content of the artifact in Excalidraw format, which will be rendered as a diagram."),
            "required": ["content_type", "excalidraw"],
        }

    content_type: Literal["excalidraw"] = "excalidraw"


ArtifactContentType = Union[
    ArtifactMarkdownContent,
    ArtifactCodeContent,
    ArtifactMermaidContent,
    ArtifactAbcContent,
    ArtifactExcalidrawContent,
]


class Artifact(BaseModel):
    class Config:
        extra = "forbid"
        json_schema_extra = {
            "description": (
                "Data for the artifact, which includes a label, content, filename, type, and version. The filename"
                " should be unique for each artifact, and the version should start at 1 and increment for each new"
                " version of the artifact. The type should be one of the specific content types and include any"
                " additional fields required for that type."
            ),
            "required": ["label", "content", "filename", "type", "version"],
        }

    label: str
    content: str
    filename: str
    type: ArtifactContentType
    version: int


# endregion


#
# region Agent
#


class ArtifactAgent:
    """
    An agent for managing artifacts.
    """

    @staticmethod
    def create_or_update_artifact(context: ConversationContext, artifact: Artifact) -> None:
        """
        Create or update an artifact with the given filename and contents.
        """
        # check if there is already an artifact with the same filename and version
        existing_artifact = ArtifactAgent.get_artifact(context, artifact.filename, artifact.version)
        if existing_artifact:
            # update the existing artifact
            artifact.version = existing_artifact.version + 1
            # try again
            ArtifactAgent.create_or_update_artifact(context, artifact)
        else:
            # write the artifact to storage
            write_model(
                _get_artifact_storage_path(context, artifact.filename) / f"artifact.{artifact.version}.json",
                artifact,
            )

    @staticmethod
    def get_artifact(context: ConversationContext, filename: str, version: int | None = None) -> Artifact | None:
        """
        Read the artifact with the given filename.
        """
        if version:
            return read_model(_get_artifact_storage_path(context, filename) / f"artifact.{version}.json", Artifact)
        else:
            return read_model(
                max(
                    _get_artifact_storage_path(context, filename).glob("artifact.*.json"),
                    key=lambda p: int(p.stem.split(".")[1]),
                ),
                Artifact,
            )

    @staticmethod
    def get_all_artifacts(context: ConversationContext) -> list[Artifact]:
        """
        Read all artifacts, will return latest version of each artifact.
        """
        artifacts: list[Artifact] = []
        artifacts_directory = _get_artifact_storage_path(context)
        if not artifacts_directory.exists() or not artifacts_directory.is_dir():
            return artifacts

        for path in artifacts_directory.iterdir():
            # each should be a directory
            if path.is_dir():
                # get the latest version of the artifact
                artifact = read_model(
                    max(path.glob("artifact.*.json"), key=lambda p: int(p.stem.split(".")[1])),
                    Artifact,
                )
                if artifact is not None:
                    artifacts.append(artifact)

        return artifacts

    @staticmethod
    def delete_artifact(context: ConversationContext, filename: str) -> None:
        """
        Delete the artifact with the given filename.
        """
        _get_artifact_storage_path(context, filename).unlink(missing_ok=True)


# endregion


#
# region Inspector
#


class ArtifactConversationInspectorStateProvider:
    display_name = "Artifacts"
    description = "Artifacts that have been co-created by the participants in the conversation. NOTE: This feature is experimental and disabled by default."

    def __init__(
        self,
        config_provider: BaseModelAssistantConfig["AssistantConfigModel"],
    ) -> None:
        self.config_provider = config_provider

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the artifacts for the conversation.
        """

        # get the configuration for the artifact agent
        config = await self.config_provider.get(context.assistant)
        if not config.agents_config.artifact_agent.enabled:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Artifacts are disabled in assistant configuration."}
            )

        # get the artifacts for the conversation
        artifacts = ArtifactAgent.get_all_artifacts(context)

        if not artifacts:
            return AssistantConversationInspectorStateDataModel(data={"content": "No artifacts available."})

        # create the data model for the artifacts
        data_model = AssistantConversationInspectorStateDataModel(
            data={"artifacts": [artifact.model_dump(mode="json") for artifact in artifacts]}
        )

        return data_model


# endregion


#
# region Helpers
#


def _get_artifact_storage_path(context: ConversationContext, filename: str | None = None) -> Path:
    """
    Get the path to the directory for storing artifacts.
    """
    path = storage_directory_for_context(context) / "artifacts"

    if not filename:
        return path

    return path / filename


# endregion
