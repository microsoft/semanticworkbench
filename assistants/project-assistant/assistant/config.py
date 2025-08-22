from typing import Annotated

import openai_client
from assistant_extensions.attachments import AttachmentsConfigModel
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.assistant_app import (
    BaseModelAssistantConfig,
)
from semantic_workbench_assistant.config import UISchema

from .utils import load_text_include


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "openai_model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max tokens",
            description=(
                "The maximum number of tokens to use for both the prompt and response. Current max supported by OpenAI"
                " is 128k tokens, but varies by model (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 64_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 8_000

    coordinator_conversation_token_limit: Annotated[
        int,
        Field(
            title="Coordinator conversation token limit",
            description="The maximum number of tokens to use for the coordinator conversation history.",
        ),
    ] = 4000

    openai_model: Annotated[
        str,
        Field(
            title="OpenAI model",
            description="The OpenAI model to use for generating responses.",
        ),
    ] = "gpt-4.1"


class PromptConfig(BaseModel):
    model_config = ConfigDict(
        title="Prompt templates",
        json_schema_extra={
            "required": [
                "coordinator_instructions",
                "team_instructions",
                "share_information_request_detection",
                "update_knowledge_digest",
                "welcome_message_generation",
            ],
        },
    )

    coordinator_instructions: Annotated[
        str,
        Field(
            title="Coordinator instructions",
            description="The instructions to give the coordinator assistant. This is added to the prompt when in coordinator mode.",  # noqa: E501
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("coordinator_instructions.md")

    team_instructions: Annotated[
        str,
        Field(
            title="Team instructions",
            description="The instructions to give the team assistant. This is added to the prompt when in team member mode.",  # noqa: E501
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("team_instructions.txt")

    detect_information_request_needs: Annotated[
        str,
        Field(
            title="Information Request detection prompt",
            description="The prompt used to detect information requests in knowledge transfer mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("detect_information_request_needs.md")

    update_knowledge_digest: Annotated[
        str,
        Field(
            title="Knowledge Digest update prompt",
            description="The prompt used to generate updated knowledge digest content.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("update_knowledge_digest.md")

    welcome_message_generation: Annotated[
        str,
        Field(
            title="Welcome Message generation prompt",
            description="The prompt used to generate a welcome message for new team conversations.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("welcome_message_generation.txt")


class CoordinatorConfig(BaseModel):
    model_config = ConfigDict(
        title="Coordinator configuration",
        json_schema_extra={
            "required": ["welcome_message", "preferred_communication_style", "max_digest_tokens"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Coordinator Welcome Message",
            description="The message to display when a coordinator starts a new knowledge transfer. {share_url} will be replaced with the actual URL.",  # noqa: E501
        ),
        UISchema(widget="textarea"),
    ] = """# Welcome to Knowledge Transfer

Welcome! I'm here to help you capture and share knowledge in a way that others can easily explore and understand.
Think of me as your personal knowledge bridge - I'll help you:

- 📚 Organize your thoughts - whether from documents, code, research papers, or brainstorming sessions
- 🔄 Establish shared understanding - I'll ask questions to ensure we're aligned on what matters most
- 🎯 Define learning objectives - so we can track progress and outcomes
- 🔍 Make your knowledge interactive - so others can explore the "why" behind decisions, alternatives considered,
  and deeper context

Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight.
I'll capture what knowledge you give me so it can be shared with your team members for them to explore at their own pace.

In the side panel, you can see your "knowledge brief". This brief will be shared with your team members and will
help them understand the content of your knowledge transfer. You can ask me to update it at any time.

To get started, let's discuss your audience. Who are you going to be sharing your knowledge with?"""  # noqa: E501

    max_digest_tokens: Annotated[
        int,
        Field(
            title="Maximum digest tokens",
            description=("The number of tokens to use for the knowledge digest. Default: 4096"),
        ),
    ] = 4_096

    preferred_communication_style: Annotated[
        str,
        Field(
            title="Preferred communication style",
            description="The preferred communication style for the assistant. This is used to tailor responses.",
        ),
        UISchema(widget="textarea"),
    ] = "Speak plainly. Keep your responses short and concise to create a more collaborative dynamic. Use no filler words or unnecessary content."  # noqa: E501


class TeamConfig(BaseModel):
    model_config = ConfigDict(
        title="Team-member configuration",
        json_schema_extra={
            "required": ["default_welcome_message", "preferred_communication_style"],
        },
    )

    default_welcome_message: Annotated[
        str,
        Field(
            title="Team Welcome message",
            description="The message to display when a user joins a knowledge transfer as a Team member. Shown after successfully joining a knowledge transfer.",  # noqa: E501
        ),
        UISchema(widget="textarea"),
    ] = "# Welcome to Your Team Conversation\n\nYou've joined as a team member. This is your personal conversation for exploring the knowledge share. You can communicate with the assistant, make information requests, and track your progress here."  # noqa: E501

    preferred_communication_style: Annotated[
        str,
        Field(
            title="Preferred communication style",
            description="The preferred communication style for the assistant. This is used to tailor responses.",
        ),
        UISchema(widget="textarea"),
    ] = "Speak plainly. Keep your responses short and concise to create a more collaborative dynamic. Use no filler words or unnecessary content. Users tend to not want to read long answers and will skip over text. Let the user ask for longer information as needed."  # noqa: E501


# Base Assistant Configuration - shared by all templates
class AssistantConfigModel(BaseModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include debug output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    prompt_config: Annotated[
        PromptConfig,
        Field(
            title="Prompt configuration",
            description="Configuration for prompt templates used throughout the assistant.",
        ),
    ] = PromptConfig()

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request configuration",
        ),
    ] = RequestConfig()

    service_config: openai_client.ServiceConfig

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety configuration",
        ),
    ] = CombinedContentSafetyEvaluatorConfig()

    attachments_config: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments configuration",
            description="Configuration for handling file attachments in messages.",
        ),
    ] = AttachmentsConfigModel()

    # Project configuration fields moved directly into AssistantConfigModel
    auto_sync_files: Annotated[
        bool,
        Field(
            title="Auto-sync files",
            description="Automatically synchronize files between linked conversations.",
        ),
    ] = True

    coordinator_config: Annotated[
        CoordinatorConfig,
        Field(
            title="Coordinator configuration",
            description="Configuration for knowledge transfer coordinators.",
        ),
    ] = CoordinatorConfig()

    team_config: Annotated[
        TeamConfig,
        Field(
            title="Team configuration",
            description="Configuration for knowledge transfer team members.",
        ),
    ] = TeamConfig()


assistant_config = BaseModelAssistantConfig(AssistantConfigModel)
