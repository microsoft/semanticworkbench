import mimetypes
from typing import Optional

import requests

from server.utils.browser_utils import SimpleTextBrowser

# ---------------------------
# Factory functions for web browser tools.
# Each function accepts a browser instance (which is assumed to provide methods such as visit_page,
# _state(), page_up(), page_down(), find_on_page(), and find_next()) and returns a callable tool.

def create_search_information_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that performs a web search query (similar to a Google search) and returns the search results.

    Args:
        browser: An instance of a browser class that provides a visit_page() method and a _state() method
                 returning a (header, content) tuple.

    Returns:
        A function that accepts:
            - query (str): The web search query.
            - filter_year (Optional[int]): [Optional] If provided, limits results to pages from that year.
        and returns a string combining the header and content from the browser.
    """
    def search_information(query: str, filter_year: Optional[int] = None) -> str:
        browser.visit_page(f"google: {query}", filter_year=filter_year)
        header, content = browser._state()
        return header.strip() + "\n=======================\n" + content
    return search_information


def create_visit_tool(browser: SimpleTextBrowser):
    """
    Creates a tool to visit a webpage at a given URL and return its text content.

    Args:
        browser: An instance of a browser class that can visit pages and retrieve its state.

    Returns:
        A function that accepts:
            - url (str): The relative or absolute URL of the webpage to visit.
        and returns the page header and content as a formatted string.
        (For YouTube URLs, this tool is expected to return a transcript.)
    """
    def visit_page(url: str) -> str:
        browser.visit_page(url)
        header, content = browser._state()
        return header.strip() + "\n=======================\n" + content
    return visit_page


def create_download_tool(browser: SimpleTextBrowser):
    """
    Creates a tool to download a file at a given URL and save it locally.

    The tool expects the URL to point to a file with one of these extensions:
    [".xlsx", ".pptx", ".wav", ".mp3", ".png", ".docx"]. After downloading, it returns the local file path.
    (Do not use this tool for .pdf, .txt, or .htm files; for those, use the visit_page tool instead.)

    Args:
        browser: The browser instance (not used here for navigation, but provided for uniformity).

    Returns:
        A function that accepts:
            - url (str): The relative or absolute URL of the file to be downloaded.
        and returns a string indicating the local path where the file was saved.
    """
    def download_file(url: str) -> str:
        # For arXiv pages, replace "abs" with "pdf" in the URL.
        if "arxiv" in url:
            url = url.replace("abs", "pdf")
        response = requests.get(url)
        content_type = response.headers.get("content-type", "")
        extension = mimetypes.guess_extension(content_type)
        if extension and isinstance(extension, str):
            new_path = f"./downloads/file{extension}"
        else:
            new_path = "./downloads/file.object"
        with open(new_path, "wb") as f:
            f.write(response.content)
        if extension and any(x in extension for x in ["pdf", "txt", "htm"]):
            raise Exception("Do not use this tool for pdf, txt, or html files: use visit_page instead.")
        return f"File was downloaded and saved under path {new_path}."
    return download_file


def create_archive_search_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that searches the Wayback Machine for an archived version of a URL close to a specified date.

    Args:
        browser: A browser instance that can navigate to URLs and retrieve state.

    Returns:
        A function that accepts:
            - url (str): The URL for which an archived snapshot is desired.
            - date (str): The target date in the format 'YYYYMMDD'.
        The tool returns a formatted string containing the archived page header and content.
    """
    def find_archived_url(url: str, date: str) -> str:
        base_api = f"https://archive.org/wayback/available?url={url}"
        archive_api = base_api + f"&timestamp={date}"
        response = requests.get(archive_api).json()
        response_no_ts = requests.get(base_api).json()
        if "archived_snapshots" in response and "closest" in response["archived_snapshots"]:
            closest = response["archived_snapshots"]["closest"]
            print("Archive found!", closest)
        elif "archived_snapshots" in response_no_ts and "closest" in response_no_ts["archived_snapshots"]:
            closest = response_no_ts["archived_snapshots"]["closest"]
            print("Archive found!", closest)
        else:
            raise Exception(f"Your URL {url=} was not archived on Wayback Machine; try a different URL.")
        target_url = closest["url"]
        browser.visit_page(target_url)
        header, content = browser._state()
        return (
            f"Web archive for URL {url}, snapshot taken at date {closest['timestamp'][:8]}:\n"
            + header.strip() + "\n=======================\n" + content
        )
    return find_archived_url


def create_page_up_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that scrolls the current webpage UP by one page-length.

    Args:
        browser: A browser instance with a page_up() method and a _state() method.

    Returns:
        A function that takes no parameters and returns the updated page content.
    """
    def page_up() -> str:
        browser.page_up()
        header, content = browser._state()
        return header.strip() + "\n=======================\n" + content
    return page_up


def create_page_down_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that scrolls the current webpage DOWN by one page-length.

    Args:
        browser: A browser instance with a page_down() method and a _state() method.

    Returns:
        A function that takes no parameters and returns the updated page content.
    """
    def page_down() -> str:
        browser.page_down()
        header, content = browser._state()
        return header.strip() + "\n=======================\n" + content
    return page_down


def create_finder_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that scrolls the viewport to the first occurrence of a search string (like Ctrl+F).

    Args:
        browser: A browser instance with a find_on_page() method and a _state() method.

    Returns:
        A function that accepts:
            - search_string (str): The string to search for on the page.
        If found, returns the page content; otherwise, returns a message indicating no match was found.
    """
    def find_on_page(search_string: str) -> str:
        find_result = browser.find_on_page(search_string)
        header, content = browser._state()
        if find_result is None:
            return header.strip() + f"\n=======================\nThe search string '{search_string}' was not found on this page."
        else:
            return header.strip() + "\n=======================\n" + content
    return find_on_page


def create_find_next_tool(browser: SimpleTextBrowser):
    """
    Creates a tool that moves to the next occurrence of a previously searched string.

    Args:
        browser: A browser instance with a find_next() method and a _state() method.

    Returns:
        A function that takes no parameters and returns the updated page content,
        or a message if no further match is found.
    """
    def find_next() -> str:
        find_result = browser.find_next()
        header, content = browser._state()
        if find_result is None:
            return header.strip() + "\n=======================\nThe search string was not found on this page."
        else:
            return header.strip() + "\n=======================\n" + content
    return find_next
