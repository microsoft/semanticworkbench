from typing import cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    message_content_from_completion,
    validate_completion,
)
from skill_library import RunContext
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill


async def generate_search_query(
    context: RunContext, search_description: str, previous_searches: list[tuple[str, str]] | None = None
) -> str:
    """Generate a search query from the search_description."""

    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    previous_searches_str = ""
    if previous_searches:
        previous_searches_str = "The previous search queries generated by the system were not good enough to satisfy the search description. Here are the previous search queries and the reasons why they weren't good enough. Use this information to generate a better search query.\n\n"

        for search_query, reasoning in previous_searches:
            previous_searches_str += f"Search query: {search_query}\nReasoning: {reasoning}\n"

    user_message_str = f"Search description: {search_description}"
    if previous_searches:
        user_message_str += f"\n\n{previous_searches_str}"

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                "You are a part of an AGI system that searches for information. Take the user's description of what they want to search for and return an appropriate search query to use in Bing. Only the top three results will be used, so make the search query detailed. Respond with just the search query.",
            ),
            create_user_message(
                user_message_str,
            ),
        ],
    }

    logger.debug("Completion call.", extra=extra_data(make_completion_args_serializable(completion_args)))
    context.log({"completion_args": make_completion_args_serializable(completion_args)})
    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        logger.debug("Completion response.", extra=extra_data({"completion": completion.model_dump()}))
        context.log({"completion": completion.model_dump()})
    except Exception as e:
        completion_error = CompletionError(e)
        context.log({"completion_error": completion_error.message})
        logger.error(
            completion_error.message,
            extra=extra_data({"completion_error": completion_error.body, "metadata": context.metadata_log}),
        )
        raise completion_error from e
    else:
        search_query = message_content_from_completion(completion).strip().strip('"')
        context.log({"search_query": search_query})
        return search_query


__default__ = generate_search_query
