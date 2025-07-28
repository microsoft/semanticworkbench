"""
Knowledge Package Service for business logic operations.

Provides business logic methods for KnowledgePackage state assessment,
presentation, achievement tracking, and conversation management.
"""

from typing import List, Optional, Tuple

from ..data import KnowledgePackage, LearningOutcomeAchievement


class KnowledgePackageManager:
    """Manager class for KnowledgePackage business logic operations."""

    @staticmethod
    def is_ready_for_transfer(package: KnowledgePackage) -> bool:
        has_basic_requirements = (
            package.knowledge_organized and package.brief is not None and package.audience is not None
        )

        if not has_basic_requirements:
            return False

        if not package.is_intended_to_accomplish_outcomes:
            return True

        return bool(package.learning_objectives) and any(
            bool(obj.learning_outcomes) for obj in package.learning_objectives
        )

    @staticmethod
    def is_actively_sharing(package: KnowledgePackage) -> bool:
        return KnowledgePackageManager.is_ready_for_transfer(package) and len(package.team_conversations) > 0

    @staticmethod
    def get_achievements_for_conversation(
        package: KnowledgePackage, conversation_id: str
    ) -> List[LearningOutcomeAchievement]:
        team_conv = package.team_conversations.get(conversation_id)
        return team_conv.outcome_achievements if team_conv else []

    @staticmethod
    def get_completion_for_conversation(package: KnowledgePackage, conversation_id: str) -> Tuple[int, int]:
        achievements = KnowledgePackageManager.get_achievements_for_conversation(package, conversation_id)
        achieved_outcome_ids = {a.outcome_id for a in achievements if a.achieved}

        total_outcomes = sum(len(obj.learning_outcomes) for obj in package.learning_objectives)
        achieved_outcomes = len(achieved_outcome_ids)

        return achieved_outcomes, total_outcomes

    @staticmethod
    def is_outcome_achieved_by_conversation(package: KnowledgePackage, outcome_id: str, conversation_id: str) -> bool:
        achievements = KnowledgePackageManager.get_achievements_for_conversation(package, conversation_id)
        return any(a.outcome_id == outcome_id and a.achieved for a in achievements)

    @staticmethod
    def get_overall_completion(package: KnowledgePackage) -> Tuple[int, int]:
        """
        Get overall completion across all team conversations.
        Returns:
            Tuple of (unique_achieved_outcomes, total_outcomes) across all team conversations
        """
        all_achieved_outcomes = set()
        for team_conv in package.team_conversations.values():
            achieved_ids = {a.outcome_id for a in team_conv.outcome_achievements if a.achieved}
            all_achieved_outcomes.update(achieved_ids)

        total_outcomes = sum(len(obj.learning_outcomes) for obj in package.learning_objectives)
        return len(all_achieved_outcomes), total_outcomes

    @staticmethod
    def get_all_linked_conversations(package: KnowledgePackage, exclude_current: Optional[str] = None) -> List[str]:
        """
        Get all conversations linked to this knowledge package.
        Returns:
            List of conversation IDs (coordinator, shared template, and all team conversations)
        """
        conversations = []

        # Add coordinator conversation
        if package.coordinator_conversation_id and package.coordinator_conversation_id != exclude_current:
            conversations.append(package.coordinator_conversation_id)

        # Add shared template conversation (though usually excluded from notifications)
        if package.shared_conversation_id and package.shared_conversation_id != exclude_current:
            conversations.append(package.shared_conversation_id)

        # Add all team conversations
        for conversation_id in package.team_conversations.keys():
            if conversation_id != exclude_current:
                conversations.append(conversation_id)

        return conversations

    @staticmethod
    def get_notification_conversations(package: KnowledgePackage, exclude_current: Optional[str] = None) -> List[str]:
        """
        Get conversations that should receive notifications (excludes shared template).
        Returns:
            List of conversation IDs that should receive notifications
        """
        conversations = []

        # Add coordinator conversation
        if package.coordinator_conversation_id and package.coordinator_conversation_id != exclude_current:
            conversations.append(package.coordinator_conversation_id)

        # Add all team conversations (but NOT shared template)
        for conversation_id in package.team_conversations.keys():
            if conversation_id != exclude_current:
                conversations.append(conversation_id)

        return conversations

    @staticmethod
    def _is_transfer_complete(package: KnowledgePackage) -> bool:
        """
        Check if knowledge transfer is complete (all outcomes achieved by at least one team member).
        Returns:
            True if all learning outcomes have been achieved by at least one team conversation
        """
        if not package.is_intended_to_accomplish_outcomes:
            return False

        achieved_outcomes, total_outcomes = KnowledgePackageManager.get_overall_completion(package)
        return total_outcomes > 0 and achieved_outcomes == total_outcomes
