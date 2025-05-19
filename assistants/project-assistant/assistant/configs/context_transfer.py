from typing import Annotated

from pydantic import Field
from semantic_workbench_assistant.config import UISchema

from ..utils import load_text_include
from .default import AssistantConfigModel, CoordinatorConfig, PromptConfig, TeamConfig


class ContextTransferPromptConfig(PromptConfig):
    """Prompt configuration specific to knowledge transfer template."""

    whiteboard_prompt: Annotated[
        str,
        Field(
            title="Knowledge Transfer Whiteboard Prompt",
            description="The prompt used to generate whiteboard content in knowledge transfer mode.",
        ),
    ] = load_text_include("context_transfer_whiteboard_prompt.txt")

    project_information_request_detection: Annotated[
        str,
        Field(
            title="Knowledge Transfer Information Request Detection Prompt",
            description="The prompt used to detect information requests in knowledge transfer mode.",
        ),
    ] = load_text_include("context_transfer_information_request_detection.txt")

    welcome_message_generation: Annotated[
        str,
        Field(
            title="Welcome Message generation prompt",
            description="The prompt used to generate a welcome message for new team conversations.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("context_transfer_welcome_message_generation.txt")


class ContextTransferCoordinatorConfig(CoordinatorConfig):
    """Coordinator configuration specific to knowledge transfer template."""

    welcome_message: Annotated[
        str,
        Field(
            title="Knowledge Transfer Coordinator Welcome Message",
            description="The message to display when a coordinator starts a new knowledge transfer project. {share_url} will be replaced with the actual URL.",
        ),
    ] = """# Welcome to Knowledge Transfer

Welcome! I'm here to help you capture and share complex information in a way that others can easily explore and understand. Think of me as your personal knowledge bridge - I'll help you:

- 📚 Organize your thoughts - whether from documents, code, research papers, or brainstorming sessions
- 🔄 Establish shared understanding - I'll ask questions to ensure we're aligned on what matters most
- 🔍 Make your knowledge interactive - so others can explore the "why" behind decisions, alternatives considered, and deeper context
- 🔗 Create shareable experiences - I'll capture what knowledge you give me so it can be shared with your team members for them to explore at their own pace using this [Knowledge Transfer link]({share_url})

Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight. I'll capture what knowledge you give me so it can be shared with your team members for them to explore at their own pace.

In the side panel, you can see your "knowledge brief". This brief will be shared with your team members and will help them understand the content of your knowledge transfer. You can ask me to update it at any time.

What knowledge would you like to transfer today?"""


class ContextTransferTeamConfig(TeamConfig):
    """Team configuration specific to knowlege transfer template."""

    default_welcome_message: Annotated[
        str,
        Field(
            title="Knowledge Transfer Team Welcome Message",
            description="The message to display when a user joins as a Team member in knowledge transfer mode.",
        ),
    ] = "# Welcome to your Knowledge Transfer space!\n\nYou now have access to the shared knowledge that has been prepared for you. This is your personal conversation for exploring your knowledge space."


class ContextTransferConfigModel(AssistantConfigModel):
    project_or_context: Annotated[str, UISchema(widget="hidden")] = "knowledge"
    Project_or_Context: Annotated[str, UISchema(widget="hidden")] = "Knowledge"

    prompt_config: Annotated[
        PromptConfig,
        Field(
            title="Prompt Configuration",
            description="Configuration for prompt templates used throughout the assistant.",
        ),
    ] = ContextTransferPromptConfig()

    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide knowledge organizers through knowledge structuring.",
        ),
    ] = True

    track_progress: Annotated[
        bool,
        Field(
            title="Track Progress",
            description="Track project progress with goals, criteria completion, and overall project state.",
        ),
    ] = False

    coordinator_config: Annotated[
        CoordinatorConfig,
        Field(
            title="Knowledge Transfer Coordinator Configuration",
            description="Configuration for coordinators in knowledge transfer mode.",
        ),
    ] = ContextTransferCoordinatorConfig()

    team_config: Annotated[
        TeamConfig,
        Field(
            title="Knowledge Transfer Team Configuration",
            description="Configuration for team members in knowledge transfer mode.",
        ),
    ] = ContextTransferTeamConfig()
