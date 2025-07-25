"""
Learning inspector for learning objectives and progress tracking.
"""

from typing import Any, List

from semantic_workbench_assistant.assistant_app import (
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

from ..common import detect_assistant_role
from ..conversation_share_link import ConversationKnowledgePackageManager
from ..storage import ShareStorage
from ..storage_models import ConversationRole


class LearningInspector:
    """
    Inspector for learning objectives and progress tracking.

    Shows learning objectives, outcomes, and completion progress.
    """

    display_name = "🎯 Learning"
    description = "Learning objectives and progress tracking"
    state_id = "objectives"

    def __init__(self, config_provider) -> None:
        self.config_provider = config_provider

    async def is_enabled(self, context: ConversationContext) -> bool:
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """Get learning objectives and progress information."""

        conversation_role = await detect_assistant_role(context)

        # Get share information
        share_id = await ConversationKnowledgePackageManager.get_associated_share_id(context)
        if not share_id:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "No active knowledge package. Start a conversation to create one."}
            )

        share = ShareStorage.read_share(share_id)

        if conversation_role == ConversationRole.COORDINATOR:
            markdown = await self._format_coordinator_objectives(share, context)
        else:
            markdown = await self._format_team_objectives(share, context)

        return AssistantConversationInspectorStateDataModel(data={"content": markdown})

    async def _format_coordinator_objectives(self, share: Any, context: ConversationContext) -> str:
        """Format learning objectives for coordinator."""

        lines: List[str] = []

        if not share or not share.learning_objectives:
            lines.append("## Learning Objectives")
            lines.append("")
            lines.append("_No learning objectives have been set up yet. When shared, the assistant will help your recipients explore the knowledge in a more open way, helping them discover the important aspects of the knowledge without specific objectives or outcomes. If you would like to have a more formal process, ask your assistant to help you create learning objectives and outcomes._")
            lines.append("")
            return "\n".join(lines)

        lines.append("## Team Progress")
        lines.append("")

        # Overall progress summary
        total_outcomes = sum(len(obj.learning_outcomes) for obj in share.learning_objectives if obj.learning_outcomes)
        if total_outcomes > 0 and share.team_conversations:
            for conv_id, team_conv in share.team_conversations.items():
                achieved, total = share.get_completion_for_conversation(conv_id)
                progress_pct = int((achieved / total * 100)) if total > 0 else 0
                lines.append(f"- **{team_conv.redeemer_name}**: {achieved}/{total} outcomes ({progress_pct}%)")
            lines.append("")

        # Detailed objectives
        lines.append("## Learning Objectives")
        for objective in share.learning_objectives:
            lines.append(f"### 🎯 {objective.name}")
            lines.append(objective.description)

            if objective.learning_outcomes:
                lines.append("")
                lines.append("#### Learning Outcomes")
                for criterion in objective.learning_outcomes:
                    # Check if any team conversation has achieved this outcome
                    achieved_by_any = any(
                        share.is_outcome_achieved_by_conversation(criterion.id, conv_id)
                        for conv_id in share.team_conversations.keys()
                    )
                    status_emoji = "✅" if achieved_by_any else "⬜"

                    # Show progress ratio for team completion
                    achieved_count = 0
                    total_team_count = len(share.team_conversations)

                    for conv_id in share.team_conversations.keys():
                        if share.is_outcome_achieved_by_conversation(criterion.id, conv_id):
                            achieved_count += 1

                    achievement_info = ""
                    if total_team_count > 0:
                        achievement_info = f" ({achieved_count}/{total_team_count})"

                    lines.append(f"- {status_emoji} {criterion.description}{achievement_info}")
            lines.append("")

        return "\n".join(lines)

    async def _format_team_objectives(self, share: Any, context: ConversationContext) -> str:
        """Format learning objectives for team members."""

        lines: List[str] = []

        if not share or not share.learning_objectives:
            lines.append("## Learning Objectives")
            lines.append("")
            lines.append("_The coordinator hasn't set up specific learning objectives for this shared knowledge. Enjoy exploring at your own pace! The assistant will guide you towards important information as you go._")
            lines.append("")
            return "\n".join(lines)

        lines.append("## Learning Objectives")
        lines.append("")

        # Show my personal progress
        conversation_id = str(context.id)
        achieved_outcomes, total_outcomes = share.get_completion_for_conversation(conversation_id)
        progress_pct = int((achieved_outcomes / total_outcomes * 100)) if total_outcomes > 0 else 0
        lines.append(f"**My Progress:** {achieved_outcomes}/{total_outcomes} outcomes achieved ({progress_pct}%)")
        lines.append("")

        for objective in share.learning_objectives:
            lines.append(f"### 🎯 {objective.name}")
            lines.append(objective.description)

            if objective.learning_outcomes:
                lines.append("")
                lines.append("#### Learning Outcomes")
                for criterion in objective.learning_outcomes:
                    # Check if I've achieved this outcome
                    achieved_by_me = share.is_outcome_achieved_by_conversation(criterion.id, conversation_id)
                    status_emoji = "✅" if achieved_by_me else "⬜"

                    completion_info = ""
                    if achieved_by_me:
                        # Find my achievement record
                        my_achievements = share.get_achievements_for_conversation(conversation_id)
                        for achievement in my_achievements:
                            if achievement.outcome_id == criterion.id and achievement.achieved:
                                completion_info = f" (achieved on {achievement.achieved_at.strftime('%Y-%m-%d')})"
                                break

                    lines.append(f"- {status_emoji} {criterion.description}{completion_info}")
            lines.append("")

        return "\n".join(lines)