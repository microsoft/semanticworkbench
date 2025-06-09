"""
Tests for the ProjectManager functionality.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from assistant.data import Project, ProjectGoal, ProjectInfo, ProjectState, SuccessCriterion
from assistant.manager import ProjectManager
from semantic_workbench_assistant.assistant_app import ConversationContext


class TestProjectManager:
    """Test the ProjectManager class."""

    @pytest.fixture
    def context(self):
        """Set up test fixtures."""
        context = AsyncMock(spec=ConversationContext)
        context.conversation = MagicMock()
        context.id = "test-conversation-id"
        return context

    @pytest.mark.asyncio
    async def test_delete_project_goal(self, context, monkeypatch):
        """Test the delete_project_goal method in ProjectManager."""
        # Setup test data
        project_id = "test-project-id"
        goal_index = 1
        goal_name = "Test Goal"
        goal_description = "Test Description"

        # Create a test project with multiple goals
        test_project = Project(
            info=None,
            brief=None,
            goals=[
                ProjectGoal(name="Goal 1", description="Description 1", priority=1, success_criteria=[]),
                ProjectGoal(
                    name=goal_name,
                    description=goal_description,
                    priority=2,
                    success_criteria=[
                        SuccessCriterion(description="Criterion 1"),
                        SuccessCriterion(description="Criterion 2", completed=True),
                    ],
                ),
                ProjectGoal(name="Goal 3", description="Description 3", priority=3, success_criteria=[]),
            ],
            whiteboard=None,
            requests=[],
        )

        # Create test project info
        test_project_info = ProjectInfo(
            project_id=project_id,
            coordinator_conversation_id="test-coordinator-id",
            completed_criteria=1,
            total_criteria=2,
            progress_percentage=50,
            version=1,
            state=ProjectState.PLANNING,
        )

        # Mock get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return project_id

        monkeypatch.setattr(
            "assistant.project_manager.ProjectManager.get_project_id", AsyncMock(side_effect=mock_get_project_id)
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
            "assistant.project_manager.ProjectStorage.read_project", MagicMock(side_effect=mock_read_project)
        )

        # Mock read_project_info
        def mock_read_project_info(proj_id):
            assert proj_id == project_id
            return test_project_info

        monkeypatch.setattr(
            "assistant.project_manager.ProjectStorage.read_project_info", MagicMock(side_effect=mock_read_project_info)
        )

        # Track if write_project and write_project_info were called with correct arguments
        write_project_called = False
        write_project_info_called = False

        # Mock write_project
        def mock_write_project(proj_id, project):
            nonlocal write_project_called
            assert proj_id == project_id
            # Verify goal was removed
            assert len(project.goals) == 2
            assert project.goals[0].name == "Goal 1"
            assert project.goals[1].name == "Goal 3"
            write_project_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ProjectStorage.write_project", MagicMock(side_effect=mock_write_project)
        )

        # Mock write_project_info
        def mock_write_project_info(proj_id, project_info):
            nonlocal write_project_info_called
            assert proj_id == project_id
            # Verify project info was updated
            assert project_info.completed_criteria == 0  # Completed criterion was in the deleted goal
            assert project_info.total_criteria == 0  # All criteria were in the deleted goal
            assert project_info.progress_percentage == 0
            assert project_info.version == 2  # Incremented
            write_project_info_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ProjectStorage.write_project_info",
            MagicMock(side_effect=mock_write_project_info),
        )

        # Mock log_project_event
        log_event_called = False

        async def mock_log_project_event(*args, **kwargs):
            nonlocal log_event_called
            log_event_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ProjectStorage.log_project_event", AsyncMock(side_effect=mock_log_project_event)
        )

        # Mock notify_project_update
        notify_called = False

        async def mock_notify_project_update(*args, **kwargs):
            nonlocal notify_called
            notify_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ProjectNotifier.notify_project_update",
            AsyncMock(side_effect=mock_notify_project_update),
        )

        # Mock refresh_all_project_uis
        refresh_called = False

        async def mock_refresh_all_project_uis(*args, **kwargs):
            nonlocal refresh_called
            refresh_called = True

        monkeypatch.setattr(
            "assistant.project_manager.ProjectStorage.refresh_all_project_uis",
            AsyncMock(side_effect=mock_refresh_all_project_uis),
        )

        # Call the method being tested
        success, goal_name_result = await ProjectManager.delete_project_goal(context, goal_index)

        # Verify the result
        assert success is True
        assert goal_name_result == goal_name

        # Verify all the expected actions were performed
        assert write_project_called
        assert write_project_info_called
        assert log_event_called
        assert notify_called
        assert refresh_called

    @pytest.mark.asyncio
    async def test_delete_project_goal_invalid_index(self, context, monkeypatch):
        """Test deleting a goal with an invalid index."""
        # Setup
        project_id = "test-project-id"
        goal_index = 5  # Out of range

        # Create a test project with fewer goals than the index
        test_project = Project(
            info=None,
            brief=None,
            goals=[
                ProjectGoal(name="Goal 1", description="Description 1", priority=1, success_criteria=[]),
                ProjectGoal(name="Goal 2", description="Description 2", priority=2, success_criteria=[]),
            ],
            whiteboard=None,
            requests=[],
        )

        # Mock get_project_id
        async def mock_get_project_id(*args, **kwargs):
            return project_id

        monkeypatch.setattr(
            "assistant.project_manager.ProjectManager.get_project_id", AsyncMock(side_effect=mock_get_project_id)
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
            "assistant.project_manager.ProjectStorage.read_project", MagicMock(side_effect=mock_read_project)
        )

        # Call the method being tested with an invalid index
        success, error_message = await ProjectManager.delete_project_goal(context, goal_index)

        # Verify the result indicates failure with appropriate error message
        assert success is False
        assert error_message is not None
        assert "Invalid goal index" in str(error_message)

    @pytest.mark.asyncio
    async def test_delete_project_goal_no_project(self, context, monkeypatch):
        """Test deleting a goal when no project is associated with the conversation."""

        # Mock get_project_id to return None
        async def mock_get_project_id(*args, **kwargs):
            return None

        monkeypatch.setattr(
            "assistant.project_manager.ProjectManager.get_project_id", AsyncMock(side_effect=mock_get_project_id)
        )

        # Call the method being tested
        success, error_message = await ProjectManager.delete_project_goal(context, 1)

        # Verify the result indicates failure with appropriate error message
        assert success is False
        assert error_message is not None
        assert "No project associated with this conversation" in str(error_message)
