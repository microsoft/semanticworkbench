from typing import cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import BaseModel
from skill_library.logging import logger
from skill_library.types import LanguageModel, Metadata


async def generate_research_plan(language_model: LanguageModel, topic: str) -> tuple[list[str], Metadata]:
    """
    Generate a research plan on a given topic. The plan will consist of a set of
    research questions to be answered.
    """

    class Output(BaseModel):
        reasoning: str
        research_questions: list[str]

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                "You are an expert research assistant. For any given topic, carefully analyze it to identify core, tangential, and nuanced areas requiring exploration. Approach the topic methodically, breaking it down into its fundamental aspects, associated themes, and interconnections. Thoroughly think through the subject step by step and aim to create a comprehensive set of research questions.",
            ),
            create_user_message(
                f"Topic: {topic}",
            ),
        ],
        "response_format": Output,
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
        research_questions = cast(Output, completion.choices[0].message.parsed).research_questions
        return research_questions, metadata
