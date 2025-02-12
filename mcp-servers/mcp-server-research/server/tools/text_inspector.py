from dataclasses import dataclass
from typing import Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

from ..utils.mdconvert import MarkdownConverter

class FileAnalysisResult(BaseModel):
    """Result of analyzing a text file."""
    content: str = Field(description="The file content or analysis")
    is_raw_content: bool = Field(description="Whether this is raw file content (True) or analysis (False)")

@dataclass
class TextInspectorDeps:
    """Dependencies for text inspection."""
    text_limit: int
    md_converter: MarkdownConverter

class FileInfo(TypedDict, total=False):
    """Structure for file analysis input"""
    file_path: str
    question: Optional[str]

# Initialize text inspector agent
text_inspector = Agent(
    'openai:gpt-4o',
    deps_type=TextInspectorDeps,
    result_type=FileAnalysisResult,
    system_prompt=(
        "You are a text analysis assistant. Analyze text files and provide detailed "
        "answers to questions about them. Format detailed answers with headings: "
        "'1. Short answer', '2. Extremely detailed answer', '3. Additional Context'"
    )
)

@text_inspector.tool
async def inspect_file(
    ctx: RunContext[TextInspectorDeps],
    file_path: str,
    question: Optional[str] = None
) -> FileAnalysisResult:
    """Analyze a text file and optionally answer questions about it.

    Args:
        ctx: Runtime context with dependencies
        file_path: Path to the file to analyze
        question: Optional question about the file content
    """
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        raise ModelRetry("Cannot process image files - use a vision model instead")

    result = ctx.deps.md_converter.convert(file_path)

    if file_path.endswith('.zip'):
        return FileAnalysisResult(
            content=result.text_content,
            is_raw_content=True
        )

    if not question:
        return FileAnalysisResult(
            content=result.text_content,
            is_raw_content=True
        )

    truncated_content = result.text_content[:ctx.deps.text_limit]
    prompt = (
        f"### {result.title}\n\n{truncated_content}\n\n"
        f"Question: {question}"
    )

    return FileAnalysisResult(
        content=prompt,
        is_raw_content=False
    )

def create_text_inspector(text_limit: int = 4000) -> tuple[Agent[TextInspectorDeps, FileAnalysisResult], TextInspectorDeps]:
    """Create and configure a text inspector agent with dependencies."""
    deps = TextInspectorDeps(
        text_limit=text_limit,
        md_converter=MarkdownConverter()
    )
    return text_inspector, deps
