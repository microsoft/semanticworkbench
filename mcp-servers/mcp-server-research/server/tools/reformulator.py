from typing import List
from typing_extensions import TypedDict
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

class FormattedResponse(BaseModel):
    """Structured response from the reformulation agent."""
    final_answer: str = Field(description="The final answer in the requested format")
    confidence: float = Field(
        description="Confidence level in the answer",
        ge=0.0,
        le=1.0
    )

@dataclass
class ReformulationDeps:
    """Dependencies for response reformulation."""
    original_task: str
    conversation_history: List[dict]

class ConversationContext(TypedDict, total=False):
    """Structure for conversation context."""
    messages: List[dict]
    original_task: str

# Initialize reformulation agent
reformulation_agent = Agent(
    'openai:gpt-4o',
    deps_type=ReformulationDeps,
    result_type=FormattedResponse,
    system_prompt="""
You analyze conversations and extract final answers in specific formats.
For numbers: Use digits, no commas, no units unless specified
For strings: No articles/abbreviations unless specified
For lists: Apply number/string rules to elements
If uncertain, estimate with confidence score
"""
)

@reformulation_agent.tool
async def format_response(
    ctx: RunContext[ReformulationDeps]
) -> FormattedResponse:
    """Format the conversation into a structured response.

    Args:
        ctx: Runtime context with conversation history and original task
    """
    formatted_messages = [{
        "role": "system",
        "content": f"""Earlier task: {ctx.deps.original_task}

Conversation transcript follows:"""
    }]

    # Add conversation history
    for msg in ctx.deps.conversation_history:
        if content := msg.get("content"):
            formatted_messages.append({
                "role": "user",
                "content": content
            })

    # Add final answer request
    formatted_messages.append({
        "role": "user",
        "content": f"""
Original task: {ctx.deps.original_task}

Provide FINAL ANSWER following these rules:
- Numbers: Use digits, no commas, no units unless specified
- Strings: No articles/abbreviations unless specified
- Lists: Apply above rules to elements
- Format: FINAL ANSWER: [answer]
- If uncertain, make educated guess and indicate lower confidence
"""
    })

    return FormattedResponse(
        final_answer=formatted_messages[-1]["content"],
        confidence=1.0  # Confidence level can be adjusted based on uncertainty
    )

def create_reformulation_agent(
    task: str,
    conversation: List[dict]
) -> tuple[Agent[ReformulationDeps, FormattedResponse], ReformulationDeps]:
    """Create and configure a reformulation agent with dependencies."""
    deps = ReformulationDeps(
        original_task=task,
        conversation_history=conversation
    )
    return reformulation_agent, deps
