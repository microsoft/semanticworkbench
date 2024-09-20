from pathlib import Path
from typing import Annotated, Any, Union

from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
    FileStorageContext,
)
from semantic_workbench_assistant.config import UISchema
from semantic_workbench_assistant.storage import read_model, read_models_in_dir, write_model

#
# region Models
#


class ArtifactAgentConfigModel(BaseModel):
    instruction_prompt: Annotated[
        str,
        Field(
            description="The prompt to provide instructions for creating or updating an artifact.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are able to create artifacts that will be shared with the others in this conversation."
        " Please include any desired new artifacts or updates to existing artifacts by providing a"
        " filename and content for each. Artifacts are automatically versioned, so if you are making"
        " an update to an existing artifact, please use the same filename. If this is an intentional"
        " variant to explore another idea, go ahead and create a new filename to reflect that. Do not"
        " include the artifacts in the assistant response, as any included in the artifacts section will"
        " be shown to all participants in a well-formatted way."
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
        schema_extra = {"description": "The content of the artifact in markdown format.", "required": ["markdown"]}

    markdown: str


class ArtifactHtmlContent(BaseModel):
    class Config:
        schema_extra = {
            "description": "The content of the artifact in HTML format, which will be rendered in a CodePen editor.",
            "required": ["html"],
        }

    html: str
    javascript: str | None = None
    css: str | None = None


class ArtifactCodeContent(BaseModel):
    class Config:
        schema_extra = {
            "description": "The content of the artifact in code format with a specified language for syntax highlighting.",
            "required": ["code", "language"],
        }

    code: str
    language: str


class ArtifactMermaidContent(BaseModel):
    class Config:
        schema_extra = {
            "description": "The content of the artifact in mermaid format, which will be rendered as a diagram.",
            "required": ["mermaid"],
        }

    mermaid: str


class ArtifactAbcContent(BaseModel):
    class Config:
        schema_extra = {
            "description": (
                "The content of the artifact in abc format, which will be rendered as sheet music, an interactive player,"
                " and available for download."
            ),
            "required": ["abc"],
        }

    abc: str


ArtifactContent = Union[
    ArtifactMarkdownContent,
    ArtifactHtmlContent,
    ArtifactCodeContent,
    ArtifactMermaidContent,
    ArtifactAbcContent,
]


class Artifact(BaseModel):
    filename: str
    content: ArtifactContent
    # metadata: dict[str, Any]

    class Config:
        schema_extra = {"required": ["filename", "content"]}


# endregion


#
# region Agent
#


class ArtifactAgent:
    """
    An agent for managing artifacts.
    """

    @staticmethod
    def create_or_update_artifact(
        context: ConversationContext, filename: str, artifact: Artifact, metadata: dict[str, Any]
    ) -> None:
        """
        Create or update an artifact with the given filename and content.
        """

        # content_dict = json.loads(content)
        # if "markdown" in content_dict:
        #     artifact_content = ArtifactMarkdownContent(**content_dict)
        # elif "html" in content_dict:
        #     artifact_content = ArtifactHtmlContent(**content_dict)
        # elif "code" in content_dict:
        #     artifact_content = ArtifactCodeContent(**content_dict)
        # elif "mermaid" in content_dict:
        #     artifact_content = ArtifactMermaidContent(**content_dict)
        # elif "abc" in content_dict:
        #     artifact_content = ArtifactAbcContent(**content_dict)
        # else:
        #     raise ValueError("Invalid content type")

        write_model(
            _get_artifact_storage_path(context, filename),
            artifact,
        )

    @staticmethod
    def get_artifact(context: ConversationContext, filename: str) -> Artifact | None:
        """
        Read the artifact with the given filename.
        """
        return read_model(_get_artifact_storage_path(context, filename), Artifact)

    @staticmethod
    def get_all_artifacts(context: ConversationContext) -> list[Artifact]:
        """
        Read all artifacts.
        """
        return list(read_models_in_dir(_get_artifact_storage_path(context), Artifact))

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
    description = "Artifacts that have been co-created by the participants in the conversation."

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the artifacts for the conversation.
        """

        # get the artifacts for the conversation
        artifacts = ArtifactAgent.get_all_artifacts(context)

        # create the data model for the artifacts
        data_model = AssistantConversationInspectorStateDataModel(
            data={
                "artifacts": [
                    {
                        "filename": artifact.filename,
                        "content": artifact.content.model_dump(mode="json"),
                    }
                    for artifact in artifacts
                ]
            }
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
    path = FileStorageContext.get(context).directory / "artifacts"
    if filename:
        path /= filename
    return path


# endregion
