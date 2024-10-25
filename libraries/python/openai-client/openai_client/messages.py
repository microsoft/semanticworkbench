from typing import Literal, Sequence

from openai.types.chat import ChatCompletionMessageParam


def truncate_messages_for_logging(
    messages: list[ChatCompletionMessageParam],
    truncate_messages_for_roles: set[Literal["user", "system", "assistant", "tool", "function"]] = {
        "user",
        "system",
        "assistant",
    },
    maximum_content_length: int = 500,
    filler_text: str = " ...truncated... ",
) -> list[dict]:
    """
    Truncates message contents for logging purposes.
    """
    results = []
    for message in messages:
        if message["role"] not in truncate_messages_for_roles:
            results.append(message)
            continue

        content = message.get("content")
        if not content:
            results.append(message)
            continue

        match content:
            case str():
                compressed = truncate_string(content, maximum_content_length, filler_text)
                message["content"] = compressed
                results.append(message)

            case list():
                compressed = process_list(content, maximum_content_length, filler_text)
                message["content"] = compressed  # type: ignore
                results.append(message)

    return results


def truncate_string(string: str, maximum_length: int, filler_text: str) -> str:
    if len(string) <= maximum_length:
        return string

    head_tail_length = (maximum_length - len(filler_text)) // 2

    return string[:head_tail_length] + filler_text + string[-head_tail_length:]


def process_list(list: Sequence, maximum_length: int, filler_text: str) -> Sequence:
    for part in list:
        for key, value in part.items():
            match value:
                case str():
                    part[key] = truncate_string(value, maximum_length, filler_text)

                case dict():
                    part[key] = process_dict(value, maximum_length, filler_text)
    return list


def process_dict(dict_: dict, maximum_length: int, filler_text: str) -> dict:
    for key, value in dict_.items():
        match value:
            case str():
                dict_[key] = truncate_string(value, maximum_length, filler_text)

            case dict():
                dict_[key] = process_dict(value, maximum_length, filler_text)
    return dict_
