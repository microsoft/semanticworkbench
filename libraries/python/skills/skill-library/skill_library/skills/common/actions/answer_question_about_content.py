from typing import Optional, cast

from openai_client import (
    CompletionError,
    create_system_message,
    create_user_message,
    extra_data,
    make_completion_args_serializable,
    validate_completion,
)
from pydantic import BaseModel
from skill_library import RunContext
from skill_library.logging import logger
from skill_library.skills.common import CommonSkill
from skill_library.types import Metadata


async def answer_question_about_content(
    context: RunContext, content: str, question: str, max_length: Optional[int] = None
) -> tuple[str, Metadata]:
    """
    Generate an answer to a question from the provided content.
    """
    common_skill = cast(CommonSkill, context.skills["common"])
    language_model = common_skill.config.language_model

    class Output(BaseModel):
        reasoning: str
        answer: str

    completion_args = {
        "model": "gpt-4o",
        "messages": [
            create_system_message(
                (
                    "You are an expert in the field and hold a piece of content you are answering questions on. When the user asks a question, provide a detailed answer based solely on your content. Reason through the content to identify relevant information and structure your answer in a clear and concise manner. If the content does not contain the answer, provide a response indicating that the information is not available."
                    "\n\nTHE CONTENT:\n\n"
                    f"{content}"
                ),
            ),
            create_user_message(
                f"Question: {question}",
            ),
        ],
        "response_format": Output,
    }
    if max_length:
        completion_args["max_tokens"] = max_length

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
        research_questions = cast(Output, completion.choices[0].message.parsed).answer
        return research_questions, metadata


__default__ = answer_question_about_content
