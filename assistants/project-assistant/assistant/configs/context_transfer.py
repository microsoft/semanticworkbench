from textwrap import dedent
from typing import Annotated

from pydantic import Field

from .default import AssistantConfigModel, CoordinatorConfig, PromptConfig, TeamConfig
from ..utils import load_text_include


class ContextTransferPromptConfig(PromptConfig):
    """Prompt configuration specific to context transfer template."""

    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
    ] = dedent("""
        You are an AI context transfer assistant that helps users (coordinators) capture and share complex information in a way that others (team members) can easily explore and understand. You're designed to:

        1. Help users organize context/knowledge from documents, code, research, or brainstorming sessions
        2. Establish shared understanding through careful questioning
        3. Make context/knowledge available by conversing with team members, so they can explore deeper context

        You should focus on helping users clarify their thoughts and structure information effectively. Ask questions to understand what aspects of their knowledge are most important to convey.
        """).strip()

    coordinator_prompt: Annotated[
        str,
        Field(
            title="Context Transfer Coordinator Prompt",
            description="The prompt used to instruct the behavior of the context transfer coordinator.",
        ),
    ] = load_text_include("context_transfer_coordinator_prompt.txt")

    team_prompt: Annotated[
        str,
        Field(
            title="Context Transfer Team Prompt",
            description="The prompt used to instruct the behavior of the context transfer team member.",
        ),
    ] = load_text_include("context_transfer_team_prompt.txt")

    whiteboard_prompt: Annotated[
        str,
        Field(
            title="Context Transfer Whiteboard Prompt",
            description="The prompt used to generate whiteboard content in context transfer mode.",
        ),
    ] = load_text_include("context_transfer_whiteboard_prompt.txt")

    project_information_request_detection: Annotated[
        str,
        Field(
            title="Context Transfer Information Request Detection Prompt",
            description="The prompt used to detect information requests in context transfer mode.",
        ),
    ] = load_text_include("context_transfer_information_request_detection.txt")


class ContextTransferCoordinatorConfig(CoordinatorConfig):
    """Coordinator configuration specific to context transfer template."""

    welcome_message: Annotated[
        str,
        Field(
            title="Context Transfer Coordinator Welcome Message",
            description="The message to display when a coordinator starts a new knowledge transfer project. {share_url} will be replaced with the actual URL.",
        ),
    ] = """# Welcome to Context Transfer

Welcome! I'm here to help you capture and share complex information in a way that others can easily explore and understand. Think of me as your personal knowledge bridge - I'll help you:

- 📚 Organize your thoughts - whether from documents, code, research papers, or brainstorming sessions
- 🔄 Establish shared understanding - I'll ask questions to ensure we're aligned on what matters most
- 🔍 Make your knowledge interactive - so others can explore the "why" behind decisions, alternatives considered, and deeper context
- 🔗 Create shareable experiences - share this link with others for a self-service way to explore your knowledge:
[Explore Knowledge Space]({share_url})

Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight. I'll capture what context you give me so it can be shared with your team members for them to explore at their own pace.

In the side panel, you can see your "context brief". This brief will be shared with your team members and will help them understand the context of your knowledge transfer. You can ask me to update it at any time.

What knowledge would you like to transfer today?"""


class ContextTransferTeamConfig(TeamConfig):
    """Team configuration specific to context transfer template."""

    welcome_message: Annotated[
        str,
        Field(
            title="Context Transfer Team Welcome Message",
            description="The message to display when a user joins as a Team member in context transfer mode.",
        ),
    ] = "# Welcome to the Knowledge Space\n\nYou now have access to the shared knowledge that has been prepared for you. Feel free to explore and ask questions to better understand the content. This is your personal conversation for interacting with the knowledge space."


# ContextTransferProjectConfig has been removed - fields integrated directly into ContextTransferConfigModel


class ContextTransferConfigModel(AssistantConfigModel):
    # Use the specialized context transfer prompt configs
    prompt_config: Annotated[
        PromptConfig,  # Use the base type for type compatibility
        Field(
            title="Prompt Configuration",
            description="Configuration for prompt templates used throughout the assistant.",
        ),
    ] = ContextTransferPromptConfig()

    # Project configuration attributes directly in config model
    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide context organizers through knowledge structuring.",
        ),
    ] = True

    # Disable progress tracking for context transfer mode
    track_progress: Annotated[
        bool,
        Field(
            title="Track Progress",
            description="Track project progress with goals, criteria completion, and overall project state.",
        ),
    ] = False

    # Use the specialized context transfer configs
    coordinator_config: Annotated[
        CoordinatorConfig,  # Use the base type for type compatibility
        Field(
            title="Context Transfer Coordinator Configuration",
            description="Configuration for coordinators in context transfer mode.",
        ),
    ] = ContextTransferCoordinatorConfig()

    team_config: Annotated[
        TeamConfig,  # Use the base type for type compatibility
        Field(
            title="Context Transfer Team Configuration",
            description="Configuration for team members in context transfer mode.",
        ),
    ] = ContextTransferTeamConfig()
