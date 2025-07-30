"""
Debug inspector for internal assistant state and knowledge digest.
"""

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from assistant.domain import KnowledgeDigestManager, ShareManager, TransferManager
from assistant.domain.conversation_preferences_manager import ConversationPreferencesManager


class DebugInspector:
    """
    Inspector for debug information and internal assistant state.

    Shows the knowledge digest and other internal information maintained by the assistant.
    """

    display_name = "🐛 Debug"
    description = "Internal assistant state and knowledge digest"
    state_id = "debug"

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get debug information for display."""

        # Get share information
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        markdown = await self._format_debug_info(share_id, context)
        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_debug_info(self, share_id: str, context: ConversationContext) -> str:
        """Format debug information including knowledge digest."""

        lines: list[str] = []

        lines.append("## Debug Information")
        lines.append("")
        lines.append("This panel shows internal information maintained by the assistant. This data is automatically")
        lines.append("generated and updated by the assistant and is not directly editable by users.")
        lines.append("")

        # Get the knowledge digest
        try:
            digest = await KnowledgeDigestManager.get_knowledge_digest(context)

            lines.append("## Knowledge Digest")
            lines.append("")
            lines.append("The knowledge digest is an internal summary of the conversation that the assistant")
            lines.append("maintains to help understand the context and key information being shared. It is")
            lines.append("automatically updated as the conversation progresses.")
            lines.append("")

            if digest and digest.content:
                lines.append("### Current Digest Content")
                lines.append("")
                lines.append("```markdown")
                lines.append(digest.content)
                lines.append("```")
                lines.append("")
            else:
                lines.append("_No knowledge digest has been generated yet. The assistant will create and update_")
                lines.append("_this automatically as the conversation develops._")
                lines.append("")

        except Exception as e:
            lines.append("## Knowledge Digest")
            lines.append("")
            lines.append(f"**Error retrieving knowledge digest:** {e!s}")
            lines.append("")

        # Add share metadata for debugging
        try:
            share = await ShareManager.get_share(context)
            if share:
                lines.append("## Share Metadata")
                lines.append("")
                lines.append(f"- **Share ID:** `{share_id}`")
                lines.append(f"- **Created:** {share.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(f"- **Last Updated:** {share.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
                lines.append(
                    f"- **Team Conversations:** {len(share.team_conversations) if share.team_conversations else 0}"
                )
                lines.append(
                    f"- **Learning Objectives:** {len(share.learning_objectives) if share.learning_objectives else 0}"
                )
                lines.append(f"- **Knowledge Organized:** {share.knowledge_organized}")
                lines.append(f"- **Ready for Transfer:** {TransferManager.is_ready_for_transfer(share)}")
                lines.append(f"- **Actively Sharing:** {TransferManager.is_actively_sharing(share)}")
                if share.coordinator_conversation_id:
                    lines.append(f"- **Conversation ID:** `{share.coordinator_conversation_id}`")
                lines.append("")
                style = await ConversationPreferencesManager.get_preferred_communication_style(context)
                lines.append(f"- **Preferred Communication Style:** {style}")

        except Exception as e:
            lines.append("## Share Metadata")
            lines.append("")
            lines.append(f"**Error retrieving share metadata:** {e!s}")
            lines.append("")

        return "\n".join(lines)
