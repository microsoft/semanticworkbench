import argparse
import os
import threading

from dotenv import load_dotenv
from huggingface_hub import login


# Update the import to use the new factory function.
from .tools.text_inspector import create_text_inspector_tool
from .tools.web_browser import create_archive_search_tool, create_find_next_tool, create_finder_tool, create_page_down_tool, create_page_up_tool, create_search_information_tool, create_visit_tool
from .utils.browser_utils import SimpleTextBrowser
from scripts.visual_qa import visualizer

# Import PydanticAI’s Agent and RunContext instead of smolagents.
from pydantic_ai import Agent, RunContext

AUTHORIZED_IMPORTS = [
    "requests",
    "zipfile",
    "os",
    "pandas",
    "numpy",
    "sympy",
    "json",
    "bs4",
    "pubchempy",
    "xml",
    "yahoo_finance",
    "Bio",
    "sklearn",
    "scipy",
    "pydub",
    "io",
    "PIL",
    "chess",
    "PyPDF2",
    "pptx",
    "torch",
    "datetime",
    "fractions",
    "csv",
]
load_dotenv(override=True)
login(os.getenv("HF_TOKEN"))

append_answer_lock = threading.Lock()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", type=str, default="o1")
    parser.add_argument("--api-base", type=str, default=None)
    parser.add_argument(
        "--question",
        type=str,
        default="How many studio albums did Mercedes Sosa release before 2007?",
    )
    return parser.parse_args()


custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
)

BROWSER_CONFIG = {
    "viewport_size": 1024 * 5,
    "downloads_folder": "downloads_folder",
    "request_kwargs": {"headers": {"User-Agent": user_agent}, "timeout": 300},
    "serpapi_key": os.getenv("SERPAPI_API_KEY"),
}
os.makedirs(f"./{BROWSER_CONFIG['downloads_folder']}", exist_ok=True)


def main():
    args = parse_args()
    text_limit = 100000

    # In PydanticAI, we pass the model identifier along with model settings.
    model_settings = {
        "max_tokens": 8192,
        "reasoning_effort": "high",
        "custom_role_conversions": custom_role_conversions,
    }
    base_model_id = args.model_id

    # Here we assume that you have created an LLM model instance that is compatible with PydanticAI.
    # For example, you might have something like: llm_model = SomeLLMModel(base_model_id, model_settings=model_settings)
    # For this example, we'll assume that 'llm_model' is available.
    llm_model = ...  # Replace with your actual LLM model initialization

    # Create the document inspection tool using the new factory function.
    document_inspection_tool = create_text_inspector_tool(model=llm_model, text_limit=text_limit)

    # Instantiate the simple text browser.
    browser = SimpleTextBrowser(**BROWSER_CONFIG)

    # Create a list of web-related tools.
    WEB_TOOLS = [
        create_search_information_tool(browser),
        create_visit_tool(browser),
        create_page_up_tool(browser),
        create_page_down_tool(browser),
        create_finder_tool(browser),
        create_find_next_tool(browser),
        create_archive_search_tool(browser),
        create_text_inspector_tool(model=llm_model, text_limit=text_limit),
    ]

    # Create the web browser agent.
    text_webbrowser_agent = Agent(
        base_model_id,
        system_prompt=(
            "You are a search agent tasked with browsing the internet to answer questions. "
            "Provide as much context as possible. Use full sentences and, if needed, tools to navigate."
        ),
        model_settings={
            "max_tokens": 8192,
            "parallel_tool_calls": True,
        }
    )
    @text_webbrowser_agent.tool
    def final_answer(ctx: RunContext[None], answer: str) -> str:
        """
        Provide a final answer to the user.
        """
        return answer

    text_webbrowser_agent.add_tools(WEB_TOOLS)

    # Update the prompt template for the managed agent.
    text_webbrowser_agent.prompt_templates = text_webbrowser_agent.prompt_templates or {}
    text_webbrowser_agent.prompt_templates.setdefault("managed_agent", {})["task"] = (
        "You are a managed agent. You can navigate to online .txt files. "
        "If a file is in another format (e.g., PDF, video), use the appropriate tool "
        "('inspect_file_as_text') to inspect it. "
        "If additional context is needed, use 'final_answer' with a clarification request."
    )

    # Create the manager agent (similar to CodeAgent in smolagents).
    manager_agent = Agent(
        base_model_id,
        system_prompt=(
            "You are a code agent responsible for orchestrating searches and document inspections. "
            "Use your tools to produce a final answer to the user question."
        ),
        model_settings=model_settings,
    )
    manager_agent.add_tools([visualizer, document_inspection_tool])

    # Register a delegate tool that calls the web browser agent.
    @manager_agent.tool
    async def delegate_search(ctx: RunContext[None], query: str) -> str:
        """
        Delegate a search query to the web browser agent and return its answer.
        """
        result = await text_webbrowser_agent.run(query)
        return result.data

    # Run the manager agent with the user's question.
    answer = manager_agent.run_sync(args.question)
    print(f"Got this answer: {answer}")


if __name__ == "__main__":
    main()
