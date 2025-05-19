import base64
import os
from typing import Any, Literal

from pydantic import BaseModel

dashboard_card_metadata_key = "_dashboard_card"


class CardContent(BaseModel):
    content_type: Literal["text/markdown", "text/plain"] = "text/markdown"
    """
    The content type of the card. This can be either "text/markdown" or "text/plain". This affects how the content is rendered.
    """
    content: str
    """
    The content of the card. This can be either plain text or markdown.
    """


class TemplateConfig(BaseModel):
    """
    Configuration for a dashboard card for an assistant service.
    This is used to define the content and appearance of the card that will be shown in the dashboard.
    """

    template_id: str
    """
    The template ID.
    """
    enabled: bool
    """
    Whether the template is enabled. If False, the template will not be shown as a card in the dashboard.
    """
    icon: str
    """
    The icon as a data URL. The icon is expected to be in PNG, JPEG, or SVG format. SVG is recommended for scalability.
    fluent v9 icons from https://react.fluentui.dev/?path=/docs/icons-catalog--docs, specifically the "20Regular" icons, is a good source.
    """
    background_color: str
    """
    The background color of the card. This should be a valid CSS color string.
    fluent v9 colors from https://react.fluentui.dev/?path=/docs/theme-colors--docs are a good source.
    """
    card_content: CardContent
    """
    The content of the card.
    """


def image_to_url(
    path: os.PathLike,
    content_type: Literal["image/png", "image/jpeg", "image/svg+xml"],
) -> str:
    """
    Reads the icon file from the given path, returning it as a data URL.

    Args:
        path (os.PathLike): The path to the icon file.
        content_type (Literal["image/png", "image/jpeg", "image/svg+xml"]): The content type of the icon file.

    Returns:
        str: The icon as a data URL.
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
    """
    Generates metadata for the dashboard card. The resulting metadata dictionary is intended to be merged
    with the assistant service metadata.

    Args:
        *templates (TemplateConfig): The dashboard configurations, one per template ID.

    Returns:
        dict: The metadata for the dashboard card.

    Example:
    ```
        assistant_service_metadata={
            **dashboard_card.metadata(
                TemplateConfig(
                    enabled=True,
                    template_id="default",
                    background_color="rgb(238, 172, 178)",
                    icon=image_to_url(pathlib.Path(__file__).parent / "assets" / "icon.svg", "image/svg+xml"),
                    card_content=CardContent(
                        content_type="text/markdown",
                        content=(pathlib.Path(__file__).parent / "assets" / "card_content.md").read_text("utf-8"),
                    ),
                )
            )
        }
    ```
    """
    template_dict = {}
    for template in templates:
        template_dict[template.template_id] = template
    return {
        dashboard_card_metadata_key: template_dict,
    }


def extract_metadata_for_dashboard_card(metadata: dict[str, Any], template_id: str) -> TemplateConfig | None:
    """
    Extracts the metadata for a specific template ID from the assistant service metadata.
    Args:
        metadata (dict[str, Any]): The assistant service metadata.
        template_id (str): The template ID to extract the metadata for.
    Returns:
        TemplateConfig | None: The metadata for the specified template ID, or None if not found.
    """
    if dashboard_card_metadata_key not in metadata:
        return None
    return metadata[dashboard_card_metadata_key].get(template_id)
