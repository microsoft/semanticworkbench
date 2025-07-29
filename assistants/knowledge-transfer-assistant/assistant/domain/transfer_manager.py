"""
Knowledge Package Service for business logic operations.

Provides business logic methods for KnowledgePackage state assessment,
presentation, achievement tracking, and conversation management.
"""

from assistant.data import KnowledgePackage

from .learning_objectives_manager import LearningObjectivesManager


class TransferManager:
    """Manager class for KnowledgePackage business logic operations."""

    @staticmethod
    def is_ready_for_transfer(package: KnowledgePackage) -> bool:
        has_basic_requirements = (
            package.knowledge_organized
            and package.brief is not None
            and package.audience is not None
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
        return (
            TransferManager.is_ready_for_transfer(package)
            and len(package.team_conversations) > 0
        )

    @staticmethod
    def _is_transfer_complete(package: KnowledgePackage) -> bool:
        """
        Check if knowledge transfer is complete (all outcomes achieved by at least one team member).
        Returns:
            True if all learning outcomes have been achieved by at least one team conversation
        """
        if not package.is_intended_to_accomplish_outcomes:
            return False

        achieved_outcomes, total_outcomes = (
            LearningObjectivesManager.get_overall_completion(package)
        )
        return total_outcomes > 0 and achieved_outcomes == total_outcomes
