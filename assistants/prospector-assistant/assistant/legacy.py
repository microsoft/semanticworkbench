import datetime

from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app.context import ConversationContext, storage_directory_for_context

_legacy_prospector_cutoff_date = datetime.datetime(2024, 10, 29, 12, 40, tzinfo=datetime.UTC)


async def provide_guidance_if_necessary(context: ConversationContext) -> None:
    """
    Check if the conversation is a legacy Prospector conversation and provide guidance to the user.
    """
    marker_path = storage_directory_for_context(context) / "legacy_prospector_check_completed"

    if marker_path.exists():
        return

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()

    conversation_response = await context.get_conversation()
    # show the message if the conversation was created before the cutoff date
    if conversation_response.created_datetime.timestamp() >= _legacy_prospector_cutoff_date.timestamp():
        return

    await context.send_messages(
        NewConversationMessage(
            content=(
                "The Prospector Assistant is transitioning to an assistant-guided experience."
                " Since your conversation started before this change, we recommend the following"
                " steps to continue with the user-guided experience:\n\n"
                " 1. Open the side panel.\n"
                " 2. Remove the Prospector Assistant. \n"
                " 3. Add the Explorer Assistant (create one if necessary).\n"
            ),
            message_type=MessageType.notice,
        )
    )
