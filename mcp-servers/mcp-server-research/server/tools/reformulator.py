from typing import List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass

@dataclass
class ReformulationContext:
    original_task: str
    inner_messages: List[dict]

class FinalAnswer(BaseModel):
    answer: str = Field(description="The final answer in the specified format")

reformulation_agent = Agent(
    'anthropic:claude-3-5-sonnet-latest',
    deps_type=ReformulationContext,
    result_type=FinalAnswer,
    system_prompt="""You are a message reformulation agent. Your task is to read conversations
    and extract or reformulate final answers in a specific format. Follow the formatting rules strictly:
    - Numbers should be expressed numerically without commas or units unless specified
    - Strings should not use articles or abbreviations unless specified
    - Lists should be comma-separated
    - Keep answers as concise as possible"""
)

@reformulation_agent.tool
def get_original_task(ctx: RunContext[ReformulationContext]) -> str:
    """Get the original task that was asked."""
    return ctx.deps.original_task

@reformulation_agent.tool
def get_conversation(ctx: RunContext[ReformulationContext]) -> str:
    """Get the conversation transcript to analyze."""
    messages_text = []
    for message in ctx.deps.inner_messages:
        if content := message.get("content"):
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        messages_text.append(item["text"])
            else:
                messages_text.append(str(content))
    return "\n".join(messages_text)

def prepare_response(original_task: str, inner_messages: List[dict]) -> str:
    """Prepare a final response from a conversation."""
    context = ReformulationContext(
        original_task=original_task,
        inner_messages=inner_messages
    )

    result = reformulation_agent.run_sync(
        f"""Extract a final answer from the conversation that answers this question: {original_task}

        Format your answer according to these rules:
        - If numeric: use digits, no commas, no units unless specified
        - If text: no articles or abbreviations unless specified
        - If list: comma-separated
        - Keep it as concise as possible
        - If unable to determine, say 'Unable to determine'""",
        deps=context
    )

    return result.data.answer
