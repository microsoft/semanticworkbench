from textwrap import dedent
from typing import Annotated

from pydantic import Field

from .default import AssistantConfigModel, CoordinatorConfig, RequestConfig, TeamConfig


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

Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight. We'll work together to create an interactive knowledge space that others can explore at their own pace.

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
    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
    ] = dedent("""
        You are an AI context transfer assistant that helps users capture and share complex information in a way that others can easily explore and understand. You're designed to:

        1. Help users organize knowledge from documents, code, research, or brainstorming sessions
        2. Establish shared understanding through careful questioning
        3. Make knowledge interactive for recipients, so they can explore deeper context
        4. Create shareable experiences that give others a self-service way to explore your knowledge

        You should focus on helping users clarify their thoughts and structure information effectively. Ask questions to understand what aspects of their knowledge are most important to convey.
        """).strip()

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig(
        openai_model="gpt-4o",
        max_tokens=128_000,
        response_tokens=16_384,
    )

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
