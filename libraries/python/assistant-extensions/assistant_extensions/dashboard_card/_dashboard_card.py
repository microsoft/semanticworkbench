import base64
import os
from typing import Any, Literal

from pydantic import BaseModel

dashboard_card_metadata_key = "_dashboard_card"


class CardContent(BaseModel):
    content_type: Literal["text/markdown", "text/plain"] = "text/markdown"
    content: str


class TemplateConfig(BaseModel):
    template_id: str
    enabled: bool
    icon: str
    background_color: str
    card_content: CardContent


def image_to_url(
    path: os.PathLike,
    content_type: Literal["image/png", "image/jpeg", "image/svg+xml"],
) -> str:
    """
    Reads the icon file from the given path, returning it as a data URL.
    """

    match content_type:
        case "image/svg+xml":
            with open(path, "r", encoding="utf-8") as icon_file:
                encoded_icon = icon_file.read().replace("\n", "").strip()
                encoded_icon = f"utf-8,{encoded_icon}"

        case _:
            with open(path, "rb") as icon_file:
                encoded_icon = base64.b64encode(icon_file.read()).decode("utf-8")
                encoded_icon = f"base64,{encoded_icon}"

    return f"data:{content_type};{encoded_icon}"


def metadata(*templates: TemplateConfig) -> dict[str, Any]:
    template_dict = {}
    for template in templates:
        template_dict[template.template_id] = template
    return {
        dashboard_card_metadata_key: template_dict,
    }
