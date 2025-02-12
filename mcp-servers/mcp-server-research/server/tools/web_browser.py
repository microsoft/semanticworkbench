from dataclasses import dataclass
from typing import Optional
import requests
import os
import mimetypes

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

from ..utils.browser_utils import SimpleTextBrowser

class WebBrowserResult(BaseModel):
    """Result from web browser operations."""
    content: str = Field(description="The content or response from the browser operation")
    header: str = Field(description="Header information about the current page/state")

@dataclass
class BrowserDependencies:
    """Dependencies for web browser operations."""
    browser: 'SimpleTextBrowser'

# Initialize web browser agent
web_browser = Agent(
    'openai:gpt-4o',
    deps_type=BrowserDependencies,
    result_type=WebBrowserResult,
    system_prompt=(
        "You are a web browsing assistant that helps navigate and extract information "
        "from web pages. Use the provided tools to search, visit pages, and analyze content."
    )
)

@web_browser.tool
async def web_search(
    ctx: RunContext[BrowserDependencies],
    query: str,
    filter_year: Optional[int] = None
) -> WebBrowserResult:
    """Perform a web search query and return results.

    Args:
        ctx: Runtime context with browser dependencies
        query: Search query to execute
        filter_year: Optional year to filter results
    """
    browser = ctx.deps.browser
    browser.visit_page(f"google: {query}", filter_year=filter_year)
    header, content = browser._state()
    return WebBrowserResult(header=header, content=content)

@web_browser.tool
async def visit_page(
    ctx: RunContext[BrowserDependencies],
    url: str
) -> WebBrowserResult:
    """Visit a webpage and return its content.

    Args:
        ctx: Runtime context with browser dependencies
        url: URL to visit
    """
    browser = ctx.deps.browser
    browser.visit_page(url)
    header, content = browser._state()
    return WebBrowserResult(header=header, content=content)

@web_browser.tool
async def download_file(
    ctx: RunContext[BrowserDependencies],
    url: str
) -> WebBrowserResult:
    """Download a file from URL.

    Args:
        ctx: Runtime context with browser dependencies
        url: URL of file to download
    """
    if any(ext in url.lower() for ext in ['.pdf', '.txt', '.htm']):
        raise ModelRetry("Use visit_page for PDF, TXT or HTML files")

    response = requests.get(url)
    content_type = response.headers.get("content-type", "")
    extension = mimetypes.guess_extension(content_type) or '.download'

    file_path = os.path.join(str(ctx.deps.browser.downloads_folder), f"file{extension}")
    with open(file_path, "wb") as f:
        f.write(response.content)

    return WebBrowserResult(
        header="Download Complete",
        content=f"File saved to {file_path}"
    )

@web_browser.tool
async def find_archived_url(
    ctx: RunContext[BrowserDependencies],
    url: str,
    date: str
) -> WebBrowserResult:
    """Find archived version of URL from Wayback Machine.

    Args:
        ctx: Runtime context with browser dependencies
        url: URL to find archive for
        date: Date in YYYYMMDD format to search for
    """
    browser = ctx.deps.browser
    archive_url = f"https://archive.org/wayback/available?url={url}&timestamp={date}"
    response = requests.get(archive_url).json()

    if "archived_snapshots" not in response or "closest" not in response["archived_snapshots"]:
        raise ModelRetry(f"URL {url} not found in Wayback Machine")

    snapshot = response["archived_snapshots"]["closest"]
    browser.visit_page(snapshot["url"])
    header, content = browser._state()

    return WebBrowserResult(
        header=f"Archive from {snapshot['timestamp'][:8]}\n{header}",
        content=content
    )

@web_browser.tool
async def page_navigation(
    ctx: RunContext[BrowserDependencies],
    direction: str
) -> WebBrowserResult:
    """Navigate pages up or down.

    Args:
        ctx: Runtime context with browser dependencies
        direction: Either 'up' or 'down'
    """
    browser = ctx.deps.browser
    if direction.lower() == 'up':
        browser.page_up()
    else:
        browser.page_down()

    header, content = browser._state()
    return WebBrowserResult(header=header, content=content)

@web_browser.tool
async def find_in_page(
    ctx: RunContext[BrowserDependencies],
    search_string: str,
    find_next: bool = False
) -> WebBrowserResult:
    """Search for text in current page.

    Args:
        ctx: Runtime context with browser dependencies
        search_string: Text to search for
        find_next: Whether to find next occurrence
    """
    browser = ctx.deps.browser
    result = browser.find_next() if find_next else browser.find_on_page(search_string)
    header, content = browser._state()

    if result is None:
        content = f"'{search_string}' not found on page"

    return WebBrowserResult(header=header, content=content)

def create_web_browser(
    start_page: Optional[str] = None,
    viewport_size: int = 1024 * 8,
    downloads_folder: str = "./downloads",
    serpapi_key: Optional[str] = None
) -> tuple[Agent[BrowserDependencies, WebBrowserResult], BrowserDependencies]:
    """Create and configure a web browser agent with dependencies."""

    # Create downloads folder if it doesn't exist
    os.makedirs(downloads_folder, exist_ok=True)

    browser = SimpleTextBrowser(
        start_page=start_page,
        viewport_size=viewport_size,
        downloads_folder=downloads_folder,
        serpapi_key=serpapi_key
    )

    deps = BrowserDependencies(browser=browser)
    return web_browser, deps
