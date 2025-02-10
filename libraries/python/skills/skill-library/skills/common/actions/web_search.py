import json

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library.logging import logger
from skill_library.types import LanguageModel, Metadata

from . import bing_search, get_content_from_url, summarize


async def generate_search_query(
    language_model: LanguageModel, search_description: str, previous_searches: list[tuple[str, str]]
) -> tuple[str, Metadata]:
    """
    Generate a search query from the search_description.
    """

    system_message = "You are a part of an AGI system that searches for information. Take the user's description of what they want to search for and return an appropriate search query to use in Bing. Only the top three results will be used, so make the search query detailed."
    if previous_searches:
        previous_search_string = "\n\n".join([
            f"Search: {search}\nResult: {description}" for search, description in previous_searches
        ])
        system_message += f"\n\nThe previous search queries didn't result in finding the information we are looking for. Take this into account and make a better search query. Previous searches:\n\n{previous_search_string}"

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_message),
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


async def web_search(
    language_model: LanguageModel, search_description: str, previous_searches: list[tuple[str, str]] = []
) -> tuple[str, Metadata]:
    """
    Bing search using the search_description. Returns summarized web content
    from the top web search results to specifically answer the search
    description. Only necessary for facts and info not contained in GPT-4.

    Sometimes the search queries that are generated internally are not good
    enough to satisfy the search description. If this is the case, you can use
    the previous_searches parameter to provide the search queries that were
    generated previously and the explanation of why the results that were
    obtained from them weren't good enough. This will help the model to generate
    a better search query.
    """

    full_metadata: Metadata = {}

    # Generate search query.
    search_query, metadata = await generate_search_query(language_model, search_description, previous_searches)
    full_metadata["generate_search_query"] = metadata

    # Search Bing.
    urls = await bing_search(search_query)

    # Summarize page content from each search result.
    results = {}
    debug_i = 0
    for url in urls:
        content = await get_content_from_url(url)
        summary, metadata = await summarize(language_model, search_description, content)
        results[url] = summary
        full_metadata[f"summarize_url_content_{debug_i}"] = metadata

        debug_i += 1

    # Summarize all pages into a final result.
    response, metadata = await summarize(language_model, search_description, json.dumps(results, indent=2))
    full_metadata["summarize_all_results"] = metadata

    return response, full_metadata
