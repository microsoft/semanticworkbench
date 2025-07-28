"""
Tools directory for Knowledge Transfer Assistant.

This module provides the ShareTools class that aggregates all tool functionality
and registers role-specific tools with the LLM.
"""

from openai_client.tools import ToolFunctions
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import ConversationRole
from .information_requests import InformationRequestTools
from .learning_objectives import LearningObjectiveTools
from .learning_outcomes import LearningOutcomeTools
from .progress_tracking import ProgressTrackingTools
from .share_setup import ShareSetupTools


class ShareTools:
    """Tools for the Knowledge Transfer Assistant to use during chat completions."""

    def __init__(self, context: ConversationContext, role: ConversationRole):
        """
        Initialize the knowledge transfer tools with the current conversation context.

        Args:
            context: The conversation context
            role: The assistant's role (ConversationRole enum)
        """
        self.context = context
        self.role = role
        self.tool_functions = ToolFunctions()

        self.share_setup = ShareSetupTools(context, role)
        self.learning_objectives = LearningObjectiveTools(context, role)
        self.learning_outcomes = LearningOutcomeTools(context, role)
        self.information_requests = InformationRequestTools(context, role)
        self.progress_tracking = ProgressTrackingTools(context, role)

        if role == "coordinator":
            self._register_coordinator_tools()
        else:
            self._register_team_tools()

    def _register_coordinator_tools(self):
        """Register coordinator-specific tools."""

        # 1. Setup phase - Define audience and organize knowledge
        self.tool_functions.add_function(
            self.share_setup.update_audience,
            "update_audience",
        )
        self.tool_functions.add_function(
            self.share_setup.set_knowledge_organized,
            "set_knowledge_organized",
        )

        # 2. Brief creation phase
        self.tool_functions.add_function(
            self.share_setup.update_brief,
            "update_brief",
        )

        # 3. Learning objectives phase
        self.tool_functions.add_function(
            self.share_setup.set_learning_intention,
            "set_learning_intention",
        )
        self.tool_functions.add_function(
            self.learning_objectives.add_learning_objective,
            "add_learning_objective",
        )
        self.tool_functions.add_function(
            self.learning_objectives.update_learning_objective,
            "update_learning_objective",
        )
        self.tool_functions.add_function(
            self.learning_objectives.delete_learning_objective,
            "delete_learning_objective",
        )

        # Individual outcome management tools
        self.tool_functions.add_function(
            self.learning_outcomes.add_learning_outcome,
            "add_learning_outcome",
        )
        self.tool_functions.add_function(
            self.learning_outcomes.update_learning_outcome,
            "update_learning_outcome",
        )
        self.tool_functions.add_function(
            self.learning_outcomes.delete_learning_outcome,
            "delete_learning_outcome",
            "Delete a learning outcome by outcome ID",
        )

        # 4. Ongoing support phase
        self.tool_functions.add_function(
            self.information_requests.resolve_information_request,
            "resolve_information_request",
        )

    def _register_team_tools(self):
        """Register team-specific tools."""
        self.tool_functions.add_function(
            self.information_requests.create_information_request,
            "create_information_request",
        )
        self.tool_functions.add_function(
            self.information_requests.delete_information_request,
            "delete_information_request",
        )
        self.tool_functions.add_function(
            self.progress_tracking.mark_learning_outcome_achieved,
            "mark_learning_outcome_achieved",
        )
        self.tool_functions.add_function(
            self.progress_tracking.report_transfer_completion,
            "report_transfer_completion",
        )


__all__ = ["ShareTools"]
