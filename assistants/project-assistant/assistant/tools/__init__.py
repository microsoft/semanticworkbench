"""
Tools directory for Knowledge Transfer Assistant.

This module provides the ShareTools class that aggregates all tool functionality
and registers role-specific tools with the LLM.
"""

from openai_client.tools import ToolFunctions
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.tools.conversation_preferences import ConversationPreferencesTools
from assistant.tools.tasks import TaskTools

from .information_requests import InformationRequestTools
from .learning_outcomes import LearningOutcomeTools
from .progress_tracking import ProgressTrackingTools
from .share_setup import ShareSetupTools


class ShareTools:
    """Tools for the Knowledge Transfer Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext):
        self.context = context
        self._tool_instances = None

    def act_tools(self) -> ToolFunctions:
        fns = ToolFunctions()

        # fns.add_function(
        #     InformationRequestTools(self.context).request_information_from_user,
        #     "request_information_from_user",
        # )

        fns.add_function(
            TaskTools(self.context).add_task,
            "add_task",
        )

        fns.add_function(
            TaskTools(self.context).update_task,
            "update_task",
        )

        fns.add_function(
            ShareSetupTools(self.context).update_audience,
            "update_audience",
        )

        fns.add_function(
            ShareSetupTools(self.context).update_audience_takeaways,
            "update_audience_takeaways",
        )

        fns.add_function(
            ShareSetupTools(self.context).update_brief,
            "update_brief",
        )

        fns.add_function(
            ShareSetupTools(self.context).create_invitation_message,
            "create_invitation_message",
        )

        # tool_functions.add_function(
        #     ShareSetupTools(self.context).set_knowledge_organized,
        #     "set_knowledge_organized",
        # )

        # tool_functions.add_function(
        #     ShareSetupTools(self.context).set_learning_intention,
        #     "set_learning_intention",
        # )
        # tool_functions.add_function(
        #     LearningObjectiveTools(self.context).add_learning_objective,
        #     "add_learning_objective",
        # )
        # tool_functions.add_function(
        #     LearningObjectiveTools(self.context).update_learning_objective,
        #     "update_learning_objective",
        # )
        # tool_functions.add_function(
        #     LearningObjectiveTools(self.context).delete_learning_objective,
        #     "delete_learning_objective",
        # )

        # tool_functions.add_function(
        #     LearningOutcomeTools(self.context).add_learning_outcome,
        #     "add_learning_outcome",
        # )
        # tool_functions.add_function(
        #     LearningOutcomeTools(self.context).update_learning_outcome,
        #     "update_learning_outcome",
        # )
        # tool_functions.add_function(
        #     LearningOutcomeTools(self.context).delete_learning_outcome,
        #     "delete_learning_outcome",
        #     "Delete a learning outcome by outcome ID",
        # )

        return fns

    def conversationalist_tools(self) -> ToolFunctions:
        """Return coordinator-specific tool functions."""
        fns = ToolFunctions()

        fns.add_function(
            InformationRequestTools(self.context).request_information_from_user,
            "request_information_from_user",
        )

        fns.add_function(
            InformationRequestTools(self.context).resolve_information_request,
            "resolve_information_request",
        )

        return fns

    def team_tools(self) -> ToolFunctions:
        """Return team-specific tool functions."""
        tool_functions = ToolFunctions()

        tool_functions.add_function(
            ConversationPreferencesTools(self.context).update_preferred_communication_style,
            "update_preferred_communication_style",
        )
        tool_functions.add_function(
            InformationRequestTools(self.context).request_information_from_coordinator,
            "create_information_request",
        )
        tool_functions.add_function(
            InformationRequestTools(self.context).delete_information_request,
            "delete_information_request",
        )
        tool_functions.add_function(
            LearningOutcomeTools(self.context).mark_learning_outcome_achieved,
            "mark_learning_outcome_achieved",
        )
        tool_functions.add_function(
            ProgressTrackingTools(self.context).report_transfer_completion,
            "report_transfer_completion",
        )

        return tool_functions


__all__ = ["ShareTools"]
