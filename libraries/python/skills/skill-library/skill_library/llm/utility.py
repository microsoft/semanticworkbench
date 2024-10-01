import logging
from typing import Iterable

import tiktoken
from openai.types.chat import ChatCompletionMessageParam


logger = logging.getLogger(__name__)


def get_token_count(model: str, string: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(string))


async def limit_messages_by_token_count(
    messages: list[ChatCompletionMessageParam],
    model: str,
    max_message_tokens: int,
) -> list[ChatCompletionMessageParam]:
    if len(messages) == 0:
        return []
    current_tokens = 0
    history_messages: list[ChatCompletionMessageParam] = []
    for message in reversed(messages):
        message_tokens = get_token_count(model=model, string=str(message.get("content")))
        current_tokens += message_tokens
        if current_tokens > max_message_tokens:
            break
        history_messages.append(message)
    history_messages.reverse()
    return history_messages


def num_tokens_from_messages(messages: Iterable[ChatCompletionMessageParam], model: str) -> int:
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        logger.warning("gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        logger.warning("gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
