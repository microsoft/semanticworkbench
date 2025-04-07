from textwrap import dedent
from typing import Annotated

from pydantic import Field

from .base import AssistantConfigModel
from .project_config import ProjectConfig, RequestConfig


class ContextTransferProjectConfig(ProjectConfig):
    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide project coordinators through context building.",
        ),
    ] = True

    invitation_message: Annotated[
        str,
        Field(
            title="Invitation Message",
            description="The message sent to users when they are invited to collaborate.",
        ),
    ] = "You've been invited to explore shared knowledge in a context transfer. Type /join to accept the invitation."


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
            title="Welcome Message",
            description="The message to display when the conversation starts.",
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

    project_config: Annotated[
        ProjectConfig,
        Field(
            title="Project Configuration",
            description="Configuration settings specific to the project assistant functionality.",
        ),
    ] = ContextTransferProjectConfig()