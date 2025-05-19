from assistant_extensions import dashboard_card, navigator
from pydantic import BaseModel
from semantic_workbench_api_model.assistant_model import AssistantTemplateModel, ServiceInfoModel
from semantic_workbench_assistant.assistant_app import ConversationContext

from .model import LocalTool


class ArgumentModel(BaseModel):
    pass


async def _get_assistant_services(_: ArgumentModel, context: ConversationContext) -> str:
    return await get_assistant_services(context)


async def get_navigator_visible_assistant_service_templates(
    context: ConversationContext,
) -> list[tuple[str, AssistantTemplateModel, str]]:
    services_response = await context.get_assistant_services()

    # filter out services that are not visible to the navigator
    # (ie. don't have a navigator description in their metadata)
    navigator_visible_service: list[tuple[ServiceInfoModel, dict[str, str]]] = [
        (service, navigator.extract_metadata_for_assistant_navigator(service.metadata) or {})
        for service in services_response.assistant_service_infos
        if navigator.extract_metadata_for_assistant_navigator(service.metadata)
    ]

    # filter out templates that don't have dashboard cards, as the navigator can't display a card to users
    # (ie. don't have dashboard card in their metadata)
    navigator_visible_service_templates = [
        (service.assistant_service_id, template, navigator_metadata[template.id])
        for (service, navigator_metadata) in navigator_visible_service
        for template in service.templates
        if dashboard_card.extract_metadata_for_dashboard_card(service.metadata, template.id)
        and navigator_metadata.get(template.id)
    ]
    return navigator_visible_service_templates


async def get_assistant_services(context: ConversationContext) -> str:
    """
    Get the list of assistants available to the user.
    """

    navigator_visible_service_templates = await get_navigator_visible_assistant_service_templates(context)

    if not navigator_visible_service_templates:
        return "No assistants currently available."

    return (
        "The following assistants are available to the user:\n\n"
        + "\n\n".join([
            f"---\n\n"
            f"assistant_service_id: {assistant_service_id}, template_id: {template.id}\n"
            f"name: {template.name}\n\n"
            f"---\n\n"
            f"{navigator_description}\n\n"
            for assistant_service_id, template, navigator_description in navigator_visible_service_templates
        ])
        + "\n\n---\n\nNOTE: There are no assistants beyond those listed above. Do not recommend any assistants that are not listed above."
    )


tool = LocalTool(name="list_assistant_services", argument_model=ArgumentModel, func=_get_assistant_services)
