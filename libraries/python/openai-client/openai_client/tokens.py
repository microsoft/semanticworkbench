import json

import tiktoken


def count_tokens(model: str, value: str | list[str]) -> int:
    """
    Get the token count for a string or list of strings.
    """
    value = json.dumps(value)
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(value))


# endregion
