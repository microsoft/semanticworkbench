from typing import Any, Callable

MessageFormatter = Callable[[str, dict[str, Any]], str]


def format_message(message: str, vars: dict[str, Any]) -> str:
    """
    Format a message with the given variables.
    """
    if message and vars:
        for key, value in vars.items():
            try:
                message = message.format(**{key: value})
            except KeyError:
                pass
    return message
