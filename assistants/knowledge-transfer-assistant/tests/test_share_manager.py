"""
Tests for the KnowledgeTransferManager functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.data import (
    KnowledgePackage,
    LearningObjective,
    LearningOutcome,

)
from assistant.domain import LearningObjectivesManager
from semantic_workbench_assistant.assistant_app import ConversationContext


class TestKnowledgeTransferManager:
    """Test the KnowledgeTransferManager class."""

    @pytest.fixture
    def context(self):
        """Set up test fixtures."""
        context = AsyncMock(spec=ConversationContext)
        context.conversation = MagicMock()
        context.id = "test-conversation-id"
        return context

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal(self, context, monkeypatch):
        """Test the delete_project_goal method in KnowledgeTransferManager."""
        # Setup test data
        project_id = "test-project-id"
        objective_index = "test-objective-id-1"
        goal_name = "Test Goal"
        goal_description = "Test Description"

        # Create a test project with multiple goals
        test_project = KnowledgePackage(
            share_id=project_id,
            brief=None,
            learning_objectives=[
                LearningObjective(name="Goal 1", description="Description 1", priority=1, learning_outcomes=[]),
                LearningObjective(
                    name=goal_name,
                    description=goal_description,
                    priority=2,
                    learning_outcomes=[
                        LearningOutcome(description="Criterion 1"),
                        LearningOutcome(description="Criterion 2"),
                    ],
                ),
                LearningObjective(name="Goal 3", description="Description 3", priority=3, learning_outcomes=[]),
            ],
            digest=None,
            requests=[],
            log=None,
        )

        # Set additional fields on the test project
        test_project.coordinator_conversation_id = "test-coordinator-id"
        # Note: completion_percentage removed from model
        test_project.version = 1
        # transfer_state field has been removed from the data model

        # Mock get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return project_id

        monkeypatch.setattr(
            "assistant.manager.KnowledgeTransferManager.get_project_id", AsyncMock(side_effect=mock_get_project_id)
        )

        # Mock require_current_user
        async def mock_require_current_user(*args, **kwargs):
            return "test-user-id"

        monkeypatch.setattr("assistant.manager.require_current_user", AsyncMock(side_effect=mock_require_current_user))

        # Mock read_project
        def mock_read_project(proj_id):
            assert proj_id == project_id
            return test_project

        monkeypatch.setattr("assistant.storage.ShareStorage.read_project", MagicMock(side_effect=mock_read_project))

        # Mock read_share_info (now returns the same project)
        def mock_read_share_info(proj_id):
            assert proj_id == project_id
            return test_project

        monkeypatch.setattr(
            "assistant.storage.ShareStorage.read_share_info", MagicMock(side_effect=mock_read_share_info)
        )

        # Track if write_project and write_project_info were called with correct arguments
        write_project_called = False
        write_project_info_called = False

        # Mock write_project
        def mock_write_project(proj_id, project):
            nonlocal write_project_called
            assert proj_id == project_id
            # Verify goal was removed
            assert len(project.learning_objectives) == 2
            assert project.learning_objectives[0].name == "Goal 1"
            assert project.learning_objectives[1].name == "Goal 3"
            write_project_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ShareStorage.write_project", MagicMock(side_effect=mock_write_project)
        )

        # Mock write_share_info (now same as write_share)
        def mock_write_share_info(proj_id, package):
            nonlocal write_project_info_called
            assert proj_id == project_id
            # Verify package was updated
            assert package.achieved_outcomes == 0  # Completed criterion was in the deleted goal
            assert package.total_outcomes == 0  # All criteria were in the deleted goal
            # Note: completion_percentage removed from model
            assert package.version == 2  # Incremented
            write_project_info_called = True

        monkeypatch.setattr(
            "assistant.storage.ShareStorage.write_share_info",
            MagicMock(side_effect=mock_write_share_info),
        )

        # Mock log_project_event
        log_event_called = False

        async def mock_log_project_event(*args, **kwargs):
            nonlocal log_event_called
            log_event_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ShareStorage.log_project_event", AsyncMock(side_effect=mock_log_project_event)
        )

        # Mock notify_project_update
        notify_called = False

        async def mock_notify_project_update(*args, **kwargs):
            nonlocal notify_called
            notify_called = True

        monkeypatch.setattr(
            "assistant.notifications.Notifications.notify_all",
            AsyncMock(side_effect=mock_notify_project_update),
        )

        # Mock refresh_all_project_uis
        refresh_called = False

        async def mock_refresh_all_project_uis(*args, **kwargs):
            nonlocal refresh_called
            refresh_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ShareStorage.refresh_all_project_uis",
            AsyncMock(side_effect=mock_refresh_all_project_uis),
        )

        # Call the method being tested
        success, goal_name_result = await LearningObjectivesManager.delete_learning_objective(context, objective_index)

        # Verify the result
        assert success is True
        assert goal_name_result == goal_name

        # Verify all the expected actions were performed
        assert write_project_called
        assert write_project_info_called
        assert log_event_called
        assert notify_called
        assert refresh_called

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal_invalid_index(self, context, monkeypatch):
        """Test deleting a goal with an invalid index."""
        # Setup
        project_id = "test-project-id"
        objective_index = "invalid-objective-id"  # Invalid ID

        # Create a test project with fewer goals than the index
        test_project = KnowledgePackage(
            share_id=project_id,
            brief=None,
            learning_objectives=[
                LearningObjective(name="Goal 1", description="Description 1", priority=1, learning_outcomes=[]),
                LearningObjective(name="Goal 2", description="Description 2", priority=2, learning_outcomes=[]),
            ],
            digest=None,
            requests=[],
            log=None,
        )

        # Mock get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return project_id

        monkeypatch.setattr(
            "assistant.project_manager.KnowledgeTransferManager.get_project_id",
            AsyncMock(side_effect=mock_get_project_id),
        )

        # Mock require_current_user
        async def mock_require_current_user(*args, **kwargs):
            return "test-user-id"

        monkeypatch.setattr(
            "assistant.project_manager.require_current_user", AsyncMock(side_effect=mock_require_current_user)
        )

        # Mock read_project
        def mock_read_project(proj_id):
            assert proj_id == project_id
            return test_project

        monkeypatch.setattr(
            "assistant.project_manager.ShareStorage.read_project", MagicMock(side_effect=mock_read_project)
        )

        # Call the method being tested with an invalid index
        success, error_message = await LearningObjectivesManager.delete_learning_objective(context, objective_index)

        # Verify the result indicates failure with appropriate error message
        assert success is False
        assert error_message is not None
        assert "Invalid goal index" in str(error_message)

    # DISABLED: delete_project_goal functionality has been removed from the codebase
    # @pytest.mark.asyncio
    async def disabled_test_delete_project_goal_no_project(self, context, monkeypatch):
        """Test deleting a goal when no project is associated with the conversation."""

        # Mock get_project_id to return None
        async def mock_get_project_id(*args, **kwargs):
            return None

        monkeypatch.setattr(
            "assistant.project_manager.KnowledgeTransferManager.get_project_id",
            AsyncMock(side_effect=mock_get_project_id),
        )

        # Call the method being tested
        success, error_message = await LearningObjectivesManager.delete_learning_objective(context, "test-objective-id")

        # Verify the result indicates failure with appropriate error message
        assert success is False
        assert error_message is not None
        assert "No project associated with this conversation" in str(error_message)
