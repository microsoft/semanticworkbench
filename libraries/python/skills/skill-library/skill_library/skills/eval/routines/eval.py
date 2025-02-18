from typing import Any, Dict, cast

from events import ErrorEvent, MessageEvent
from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    message_content_from_completion,
    validate_completion,
)
from skill_library import AskUserFn, EmitFn, RunContext, RunRoutineFn
from skill_library.skills.common import CommonSkill


async def main(
    context: RunContext,
    routine_state: dict[str, Any],
    emit: EmitFn,
    run: RunRoutineFn,
    ask_user: AskUserFn,
    content: str,
    scale: Dict[int, str],
) -> str:
    """Rate the given content using the provided scale. The scale is a dictionary where each key is an integer representing a rating and each value is a description of what that rating means."""
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    scale_description = "; ".join([f"{key}: {value}" for key, value in scale.items()])
    system_message = (
        "You are a content rater. Your job is to rate the given content based "
        "on the provided scale. Provide just the numeric score. "
        f"The scale is as follows: {scale_description}."
    )

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(system_message),
            create_user_message(content),
        ],
        "max_tokens": 10,  # We only need a short response for a rating.
    }

    try:
        completion = await language_model.beta.chat.completions.parse(
            **completion_args,
        )
        validate_completion(completion)
        rating = message_content_from_completion(completion).strip()
    except Exception as e:
        completion_error = CompletionError(e)
        emit(ErrorEvent(message="Failed to rate the content."))
        raise completion_error from e

    emit(MessageEvent(message=f"The content is rated as: {rating}"))
    context.log("rate_content", {"content": content, "scale": scale, "rating": rating})

    return rating
