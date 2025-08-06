from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import InspectorTab
from assistant.domain.share_manager import ShareManager
from assistant.notifications import Notifications
from assistant.storage import ShareStorage


class ThoughtsManager:
    @staticmethod
    async def get_assistant_thoughts(
        context: ConversationContext,
    ) -> list[str]:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return []
        return ShareStorage.read_assistant_thoughts(share_id)

    @staticmethod
    async def add_assistant_thoughts(
        context: ConversationContext,
        thoughts: list[str],
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.add_assistant_thoughts(share_id, thoughts)

        await Notifications.notify(context, f"Added {len(thoughts)} assistant thoughts.")
        await Notifications.notify_state_update(context, [InspectorTab.DEBUG])

    @staticmethod
    async def remove_assistant_thought(
        context: ConversationContext,
        thought: str,
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.remove_assistant_thought(share_id, thought)
        await Notifications.notify(context, "Forgot something.")
        await Notifications.notify_state_update(context, [InspectorTab.DEBUG])
