from assistant.data import Share

from .learning_objectives_manager import LearningObjectivesManager


class TransferManager:
    @staticmethod
    def is_ready_for_transfer(share: Share) -> bool:
        has_basic_requirements = share.knowledge_organized and share.brief is not None and share.audience is not None

        if not has_basic_requirements:
            return False

        if not share.is_intended_to_accomplish_outcomes:
            return True

        return bool(share.learning_objectives) and any(bool(obj.learning_outcomes) for obj in share.learning_objectives)

    @staticmethod
    def is_actively_sharing(share: Share) -> bool:
        return TransferManager.is_ready_for_transfer(share) and len(share.team_conversations) > 0

    @staticmethod
    def _is_transfer_complete(share: Share) -> bool:
        """
        Check if knowledge transfer is complete (all outcomes achieved by at least one team member).
        Returns:
            True if all learning outcomes have been achieved by at least one team conversation
        """
        if not share.is_intended_to_accomplish_outcomes:
            return False

        achieved_outcomes, total_outcomes = LearningObjectivesManager.get_overall_completion(share)
        return total_outcomes > 0 and achieved_outcomes == total_outcomes
