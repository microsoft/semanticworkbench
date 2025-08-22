from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.data import ConversationPreferences, ConversationRole, InspectorTab
from assistant.domain.share_manager import ShareManager
from assistant.notifications import Notifications
from assistant.storage import ConversationStorage


class ConversationPreferencesManager:
    @staticmethod
    async def update_preferred_communication_style(
        context: ConversationContext,
        preferred_communication_style: str,
    ) -> None:
        """
        Update the preferences for a conversation.
        """
        preferences = ConversationStorage.read_conversation_preferences(context)

        # Set the default preferences based on the assistant config.
        if not preferences:
            config = await assistant_config.get(context.assistant)
            role = await ShareManager.get_conversation_role(context)
            if role == ConversationRole.COORDINATOR:
                style = config.coordinator_config.preferred_communication_style
            else:
                style = config.team_config.preferred_communication_style
            preferences = ConversationPreferences(
                preferred_communication_style=style,
            )

        preferences.preferred_communication_style = preferred_communication_style.strip()
        ConversationStorage.write_conversation_preferences(context, preferences)

        await Notifications.notify(context, "Preferred communication style updated.")
        await Notifications.notify_all_state_update(context, [InspectorTab.DEBUG])

    @staticmethod
    async def get_preferred_communication_style(context: ConversationContext) -> str:
        """
        Get the preferred communication style for a conversation.
        """
        preferences = ConversationStorage.read_conversation_preferences(context)
        if preferences and preferences.preferred_communication_style:
            return preferences.preferred_communication_style

        # Return the default from the assistant config if not set.
        config = await assistant_config.get(context.assistant)
        role = await ShareManager.get_conversation_role(context)
        if role == ConversationRole.COORDINATOR:
            return config.coordinator_config.preferred_communication_style
        else:
            return config.team_config.preferred_communication_style
