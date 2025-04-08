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
            description="The message to display after a user has been assigned the Coordinator role in context transfer mode.",
        ),
    ] = "Welcome to Context Transfer mode as a Coordinator! You can organize and structure knowledge to be shared with others. Upload files, add context, and create an interactive knowledge space that others can explore."

    context_building_prompt: Annotated[
        str,
        Field(
            title="Context Building Prompt",
            description="The message used to help coordinators organize their knowledge context.",
        ),
    ] = """Let's organize your knowledge context. Here are some ways to structure your information:

- Key concepts: What are the fundamental ideas you want to convey?
- Decision rationale: What choices were made and why?
- Alternatives considered: What other approaches were evaluated?
- Background context: What information might others need to understand your domain?

How would you like to structure your knowledge transfer?"""


class ContextTransferTeamConfig(TeamConfig):
    """Team configuration specific to context transfer template."""

    welcome_message: Annotated[
        str,
        Field(
            title="Context Transfer Team Welcome Message",
            description="The message to display when a user joins as a Team member in context transfer mode.",
        ),
    ] = "Welcome to the shared knowledge space! You can now explore the context that has been prepared for you. Feel free to ask questions to understand the knowledge better."

    upload_notification: Annotated[
        str,
        Field(
            title="Upload Notification",
            description="The message displayed when uploading a file in context transfer mode.",
        ),
    ] = "Your file has been uploaded to the knowledge space. It will be incorporated into the context for exploration."


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

    welcome_message: Annotated[
        str,
        Field(
            title="Initial Setup Welcome Message",
            description="The message displayed when the context transfer assistant first starts, before any role is assigned.",
        ),
    ] = dedent("""
        Welcome! I'm here to help you capture and share complex information in a way that others can easily explore and understand. Think of me as your personal knowledge bridge - I'll help you:
        
        - 📚 **Organize your thoughts** - whether from documents, code, research papers, or brainstorming sessions
        - 🔄 **Establish shared understanding** - I'll ask questions to ensure we're aligned on what matters most
        - 🔍 **Make your knowledge interactive** - so others can explore the "why" behind decisions, alternatives considered, and deeper context
        - 🔗 **Create shareable experiences** - when we're done, share a link that gives others a self-service way to explore your knowledge
        
        Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight. We'll work together to create an interactive knowledge space that others can explore at their own pace.
        
        What knowledge would you like to transfer today?
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

    invitation_message: Annotated[
        str,
        Field(
            title="Invitation Message",
            description="The message sent to users when they are invited to explore a knowledge context.",
        ),
    ] = "You've been invited to explore shared knowledge in a context transfer. Type /join to accept the invitation."

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
