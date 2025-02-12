import argparse
import os
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .tools.text_inspector import FileAnalysisResult, TextInspectorDeps, create_text_inspector
from .tools.visual_qa import ImageAnalysisResult, VisualDependencies, create_visual_qa_agent
from .tools.web_browser import BrowserDependencies, WebBrowserResult, create_web_browser

load_dotenv(override=True)

@dataclass
class AppDependencies:
    text_inspector_agent: Agent[TextInspectorDeps, FileAnalysisResult]
    visual_qa_agent: Agent[VisualDependencies, ImageAnalysisResult]
    web_browser_agent: Agent[BrowserDependencies, WebBrowserResult]
    text_inspector_deps: TextInspectorDeps
    visual_qa_deps: VisualDependencies
    web_browser_deps: BrowserDependencies

class SearchResult(BaseModel):
    answer: str = Field(description="Final answer to the query")
    confidence: float = Field(description="Confidence in the answer", ge=0, le=1)
    sources: List[str] = Field(description="Sources used to find the answer")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="openai:gpt-4o")
    parser.add_argument("--question", type=str, default="How many studio albums did Mercedes Sosa release before 2007?")
    return parser.parse_args()

BROWSER_CONFIG = {
    "viewport_size": 1024 * 5,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "timeout": 300,
    }
}

# Initialize coordinator agent to manage other agents
coordinator = Agent[AppDependencies, SearchResult](
    'openai:gpt-4o',
    deps_type=AppDependencies,
    result_type=SearchResult,
    system_prompt="""
    You coordinate specialized agents to answer questions:
    - Web browser agent for internet searches
    - Visual QA agent for image analysis
    - Text inspector for document analysis

    Choose the appropriate agent(s) based on the task and combine their results.
    """
)

@coordinator.tool
async def search_web(
    ctx: RunContext[AppDependencies],
    query: str
) -> str:
    """Search the web using the web browser agent."""
    result = await ctx.deps.web_browser_agent.run(
        query,
        deps=ctx.deps.web_browser_deps
    )
    return result.data.content

@coordinator.tool
async def analyze_image(
    ctx: RunContext[AppDependencies],
    image_path: str,
    question: Optional[str] = None
) -> str:
    """Analyze an image using the visual QA agent."""
    result = await ctx.deps.visual_qa_agent.run(
        question or "Describe this image",
        deps=ctx.deps.visual_qa_deps
    )
    return result.data.content

@coordinator.tool
async def inspect_text(
    ctx: RunContext[AppDependencies],
    file_path: str,
    question: Optional[str] = None
) -> str:
    """Inspect a text document using the text inspector agent."""
    result = await ctx.deps.text_inspector_agent.run(
        question or "Analyze this document",
        deps=ctx.deps.text_inspector_deps
    )
    return result.data.content

def create_app_dependencies(model: str) -> AppDependencies:
    """Create and configure all agents and their dependencies."""
    os.makedirs(BROWSER_CONFIG["downloads_folder"], exist_ok=True)

    text_inspector_agent, text_inspector_deps = create_text_inspector()
    visual_qa_agent, visual_qa_deps = create_visual_qa_agent()
    web_browser_agent, web_browser_deps = create_web_browser(
            **BROWSER_CONFIG,
            serpapi_key=os.getenv("SERPAPI_API_KEY")
        )

    return AppDependencies(
        text_inspector_agent=text_inspector_agent,
        visual_qa_agent=visual_qa_agent,
        web_browser_agent=web_browser_agent,
        text_inspector_deps=text_inspector_deps,
        visual_qa_deps=visual_qa_deps,
        web_browser_deps=web_browser_deps
    )

async def main():
    args = parse_args()
    deps = create_app_dependencies(args.model)

    result = await coordinator.run(args.question, deps=deps)
    print(f"Answer: {result.data.answer}")
    print(f"Confidence: {result.data.confidence}")
    print(f"Sources: {', '.join(result.data.sources)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
