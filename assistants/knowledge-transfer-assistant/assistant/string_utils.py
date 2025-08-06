from typing import Any

from liquid import Template


def render(template: str, vars: dict[str, Any] = {}) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    parsed = template
    if not vars:
        return template
    liquid_template = Template(template)
    parsed = liquid_template.render(**vars)
    return parsed
