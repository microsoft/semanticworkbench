from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class ArtifactsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description=(
                "The artifact support is experimental and disabled by default. Enable it to poke at"
                " the early features, but be aware that you may lose data or experience unexpected"
                " behavior.\n\n**NOTE: This feature requires an OpenAI or Azure OpenAI service that"
                " supports Structured Outputs with response formats.**\nSupported models\n- OpenAI:"
                " gpt-4o or gpt-4o-mini > 2024-08-06\n- Azure OpenAI: gpt-4o > 2024-08-06"
            )
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
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in markdown format. Use this type for any general text that"
                " does not match another, more specific type."
            ),
            "required": ["content_type"],
        },
    )

    content_type: Literal["markdown"] = "markdown"


class ArtifactCodeContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in code format with a specified language for syntax highlighting."
            ),
            "required": ["content_type", "language"],
        },
    )

    content_type: Literal["code"] = "code"
    language: str


class ArtifactMermaidContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": "The content of the artifact in mermaid format, which will be rendered as a diagram.",
            "required": ["content_type"],
        },
    )

    content_type: Literal["mermaid"] = "mermaid"


class ArtifactAbcContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "The content of the artifact in abc format, which will be rendered as sheet music, an interactive player,"
                " and available for download."
            ),
            "required": ["content_type"],
        },
    )

    content_type: Literal["abc"] = "abc"


class ArtifactExcalidrawContent(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": ("The content of the artifact in Excalidraw format, which will be rendered as a diagram."),
            "required": ["content_type", "excalidraw"],
        },
    )

    content_type: Literal["excalidraw"] = "excalidraw"


ArtifactContentType = Union[
    ArtifactMarkdownContent,
    ArtifactCodeContent,
    ArtifactMermaidContent,
    ArtifactAbcContent,
    ArtifactExcalidrawContent,
]


class Artifact(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "Data for the artifact, which includes a label, content, filename, type, and version. The filename"
                " should be unique for each artifact, and the version should start at 1 and increment for each new"
                " version of the artifact. The type should be one of the specific content types and include any"
                " additional fields required for that type."
            ),
            "required": ["label", "content", "filename", "type", "version"],
        },
    )

    label: str
    content: str
    filename: str
    type: ArtifactContentType
    version: int
