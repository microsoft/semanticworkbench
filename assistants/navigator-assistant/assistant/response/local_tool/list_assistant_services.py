from assistant_extensions import navigator
from pydantic import BaseModel
from semantic_workbench_assistant.assistant_app import ConversationContext

from .model import LocalTool


class ArgumentModel(BaseModel):
    pass


async def get_assistant_services(_: ArgumentModel, context: ConversationContext) -> str:
    """
    Get the list of assistants available to the user.
    """

    services_response = await context.get_assistant_services()

    navigator_visible_services = [
        (service, navigator.extract_metadata_for_assistant_navigator(service.metadata) or {})
        for service in services_response.assistant_service_infos
        if navigator.extract_metadata_for_assistant_navigator(service.metadata)
    ]

    if not navigator_visible_services:
        return "No assistants currently available."

    return "The following assistants are available:\n\n" + "\n\n".join([
        f"---\n\n"
        f"assistant_service_id: {service.assistant_service_id}, template_id: {template.id}\n"
        f"name: {template.name}\n\n"
        f"---\n\n"
        f"{metadata_for_navigator.get(template.id, '')}\n\n"
        for service, metadata_for_navigator in navigator_visible_services
        for template in service.templates
    ])


tool = LocalTool(name="list_assistant_services", argument_model=ArgumentModel, func=get_assistant_services)
