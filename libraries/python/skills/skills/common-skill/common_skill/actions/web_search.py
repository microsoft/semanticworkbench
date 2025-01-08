import json
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library.types import LanguageModel, Metadata

from ..logging import logger


async def generate_search_query(language_model: LanguageModel, search_description: str) -> tuple[str, Metadata]:
    """Generate a search query from the search_description."""
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                "You are a part of an AGI system that searches for information. Take the user's description of what they want to search for and return an appropriate search query to use in Bing. Only the top three results will be used, so make the search query detailed.",
            ),
            create_user_message(
                f"{search_description}",
            ),
        ],
    }

    metadata = {}
    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        search_query = message_content_from_completion(completion).strip().strip('"')
        return search_query, metadata


async def summarize_results(
    language_model: LanguageModel, search_description: str, results: str
) -> tuple[str, Metadata]:
    """Summarize the search results to answer the search description."""
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                (
                    "You are a web page content extractor and summarizer. Extract the relevant information to answer the user's query.\n\n"
                    f"CONTENT:\n{json.dumps(results)}"
                )
            ),
            create_user_message(search_description),
        ],
    }

    metadata = {}
    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        return message_content_from_completion(completion), metadata


async def summarize_all_results(
    language_model: LanguageModel, search_description: str, results: dict[str, str]
) -> tuple[str, Metadata]:
    """Summarize all search results to answer the search description."""
    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(f"Summarize the following content to answer the user's query: {search_description}"),
            create_user_message(json.dumps(results)),
        ],
    }

    metadata = {}
    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    metadata["completion_args"] = make_completion_args_serializable(completion_args)
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        metadata["completion"] = completion.model_dump()
    except Exception as e:
        completion_error = CompletionError(e)
        metadata["completion_error"] = completion_error.message
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": metadata}),
        )
        raise completion_error from e
    else:
        return message_content_from_completion(completion), metadata


async def web_search(language_model: LanguageModel, search_description: str) -> tuple[str, Metadata]:
    """Bing search using the search_description. Returns summarized web content
    from the top web search results to specifically answer the search
    description. Only necessary for facts and info not contained in GPT-4."""

    full_metadata: Metadata = {}

    search_query, metadata = await generate_search_query(language_model, search_description)
    full_metadata["generate_search_query"] = metadata

    # Use BingAPI to search.
    # Get Bing search subscription key.
    load_dotenv()
    subscription_key = os.getenv("BING_SEARCH_SUBSCRIPTION_KEY")
    if not subscription_key:
        raise Exception("BING_SEARCH_SUBSCRIPTION_KEY not found in .env.")
    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": search_query, "textDecorations": False}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    values = search_results.get("webPages", {}).get("value", "")[:7]
    urls = [v["url"] for v in values]
    results = {}

    debug_i = 0
    for url in urls:
        # Get webpage content from url.
        try:
            response = requests.get(url)
            if response.status_code >= 200 and response.status_code < 300:
                soup = BeautifulSoup(response.text, "html.parser")
                content = soup.get_text(separator="\n", strip=True)
                # Get first 5000 characters.
                # TODO: We can RAG or something instead of this scrappy thing.
                content = content[:5000]

                # Summarize search content.
                summary, metadata = await summarize_results(language_model, search_description, content)
                full_metadata[f"summarize_results_{debug_i}"] = metadata
                results[url] = summary
            else:
                results[url] = f"Error: {response.status_code}"
        except Exception as e:
            results[url] = f"Error: {e}"

        debug_i += 1

    # Summarize all results.
    response, metadata = await summarize_all_results(language_model, search_description, results)
    full_metadata["summarize_all_results"] = metadata

    return response, full_metadata
