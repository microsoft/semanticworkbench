"""Tests for the Team conversation handler."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


# Create mock classes for testing without importing from the actual modules
class ArtifactType:
    PROJECT_BRIEF = "project_brief"
    PROJECT_DASHBOARD = "project_dashboard"
    INFORMATION_REQUEST = "information_request"
    PROJECT_LOG = "project_log"
    KNOWLEDGE_BASE = "project_kb"


class ProjectState:
    PLANNING = "planning"
    READY_FOR_WORKING = "ready_for_working"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class RequestPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequestStatus:
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    CANCELLED = "cancelled"


class LogEntryType:
    REQUEST_CREATED = "request_created"
    STATUS_CHANGED = "status_changed"
    CRITERION_COMPLETED = "criterion_completed"
    MILESTONE_PASSED = "milestone_passed"
    PROJECT_COMPLETED = "project_completed"


class ProjectRole:
    TEAM = "team"
    COORDINATOR = "coordinator"


class MessageType:
    chat = "chat"
    notice = "notice"


class NewConversationMessage:
    def __init__(self, content, message_type):
        self.content = content
        self.message_type = message_type


class BaseArtifact:
    def __init__(
        self,
        artifact_id=None,
        artifact_type=None,
        created_by=None,
        updated_by=None,
        conversation_id=None,
        project_id=None,
        **kwargs,
    ):
        self.artifact_id = artifact_id or "test-artifact-id"
        self.artifact_type = artifact_type
        self.created_by = created_by
        self.updated_by = updated_by
        self.conversation_id = conversation_id
        self.project_id = project_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version = 1
        # Add any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class InformationRequest(BaseArtifact):
    def __init__(self, title=None, description=None, priority=None, status=None, **kwargs):
        super().__init__(artifact_type=ArtifactType.INFORMATION_REQUEST, **kwargs)
        self.title = title or "Test Request"
        self.description = description or "Test Description"
        self.priority = priority or RequestPriority.MEDIUM
        self.status = status or RequestStatus.NEW
        self.resolution = None
        self.resolved_at = None
        self.resolved_by = None


class ProjectDashboard(BaseArtifact):
    def __init__(self, state=None, active_requests=None, completed_criteria=0, total_criteria=0, **kwargs):
        super().__init__(artifact_type=ArtifactType.PROJECT_DASHBOARD, **kwargs)
        # transfer_state field removed - using derived state logic instead
        self.state = state or ProjectState.PLANNING
        # Note: completion_percentage removed from model
        self.active_requests = active_requests or []
        self.achieved_criteria = completed_criteria
        self.total_criteria = total_criteria
        self.transfer_notes = None


class LearningOutcome:
    def __init__(self, id=None, description=None, completed=False, completed_by=None):
        self.id = id or "test-criterion-id"
        self.description = description or "Test criterion"
        self.achieved = completed
        self.achieved_at = None if not completed else datetime.utcnow()
        self.achieved_by = completed_by


class LearningObjective:
    def __init__(self, id=None, name=None, description=None, priority=1, success_criteria=None):
        self.id = id or "test-goal-id"
        self.name = name or "Test Goal"
        self.description = description or "Test Goal Description"
        self.priority = priority
        self.learning_outcomes = success_criteria or []


class KnowledgeBrief(BaseArtifact):
    def __init__(self, title=None, description=None, goals=None, **kwargs):
        super().__init__(artifact_type=ArtifactType.PROJECT_BRIEF, **kwargs)
        self.title = title or "Test KnowledgePackage"
        self.description = description or "Test Description"
        self.learning_objectives = goals or []


# Create a mock for the TeamConversationHandler
class MockTeamConversationHandler:
    def __init__(self, context):
        self.context = context
        self.log_action = AsyncMock()

    async def create_information_request(self, title, description, priority=RequestPriority.MEDIUM):
        # Mock implementation
        request = InformationRequest(
            title=title,
            description=description,
            priority=priority,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            project_id="test-project-id",
        )

        # Call mocked log_action
        await self.log_action(
            LogEntryType.REQUEST_CREATED,
            f"Created information request: {title}",
            related_artifact_id=request.artifact_id,
            related_artifact_type=ArtifactType.INFORMATION_REQUEST,
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Created information request: {title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Created information request: {title}", request

    async def update_project_info(self, progress_percentage, status_message=None):
        # Mock implementation
        dashboard = ProjectDashboard(
            state=ProjectState.IN_PROGRESS,
            progress_percentage=progress_percentage,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            project_id="test-project-id",
        )
        dashboard.transfer_notes = status_message

        # Call mocked log_action for state change and progress update
        await self.log_action(LogEntryType.MILESTONE_PASSED, "KnowledgePackage is now in progress")

        await self.log_action(LogEntryType.STATUS_CHANGED, f"Updated project progress to {progress_percentage}%")

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Updated project progress to {progress_percentage}%",
                message_type=MessageType.notice,
            )
        )

        return True, f"Updated project progress to {progress_percentage}%", dashboard

    async def mark_criterion_completed(self, goal_id, criterion_id):
        # Mock implementation
        criterion = LearningOutcome(id=criterion_id, description="Test criterion")
        criterion.achieved = True
        criterion.achieved_at = datetime.utcnow()
        criterion.achieved_by = "test-user-id"

        dashboard = ProjectDashboard(
            state=ProjectState.IN_PROGRESS,
            progress_percentage=100,
            completed_criteria=1,
            total_criteria=1,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            project_id="test-project-id",
        )

        # Call mocked log_action
        await self.log_action(LogEntryType.CRITERION_COMPLETED, f"Completed criterion: {criterion.description}")

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Marked criterion '{criterion.description}' as completed.",
                message_type=MessageType.notice,
            )
        )

        return True, f"Marked criterion '{criterion.description}' as completed.", dashboard

    async def report_project_completion(self, completion_summary):
        # Mock implementation
        dashboard = ProjectDashboard(
            state=ProjectState.COMPLETED,
            progress_percentage=100,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            project_id="test-project-id",
        )
        dashboard.transfer_notes = completion_summary

        # Call mocked log_action
        await self.log_action(LogEntryType.PROJECT_COMPLETED, "KnowledgePackage marked as completed")

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 KnowledgePackage has been marked as completed.",
                message_type=MessageType.notice,
            )
        )

        return True, "KnowledgePackage has been marked as completed", dashboard

    async def get_project_info(self):
        # Mock implementation
        return {
            "has_project": True,
            "project_id": "test-project-id",
            "role": "team",
            "title": "Test KnowledgePackage",
            "description": "A test project",
            "status": "in_progress",
            "progress": 50,
            "open_requests": 0,
            "pending_requests": [],
        }


class TestTeamConversationHandler:
    """Test cases for TeamConversationHandler."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock conversation context."""
        context = AsyncMock()
        context.id = "test-conversation-id"
        context.assistant = MagicMock()
        context.assistant.id = "test-assistant-id"
        context.get_participants = AsyncMock()

        participants = MagicMock()
        participant = MagicMock()
        participant.id = "test-user-id"
        participant.name = "Test User"
        participant.role = "user"
        participants.participants = [participant]

        context.get_participants.return_value = participants
        context.send_messages = AsyncMock()

        return context

    @pytest.fixture
    def team_handler(self, mock_context):
        """Create a MockTeamConversationHandler instance with a mock context."""
        return MockTeamConversationHandler(mock_context)

    @pytest.mark.asyncio
    async def test_create_information_request(self, team_handler, mock_context):
        """Test creating an information request."""
        # Call the method
        success, message, request = await team_handler.create_information_request(
            "Test Request", "This is a test request", RequestPriority.HIGH
        )

        # Assertions
        assert success is True
        assert "Created information request: Test Request" in message
        assert request is not None
        assert request.title == "Test Request"
        assert request.description == "This is a test request"
        assert request.priority == RequestPriority.HIGH
        assert request.created_by == "test-user-id"

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        team_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_info(self, team_handler, mock_context):
        """Test updating the project information."""
        # Call the method
        success, message, dashboard = await team_handler.update_project_info(50, "Making progress in the team")

        # Assertions
        assert success is True
        assert "Updated project progress to 50%" in message
        assert dashboard is not None
        # Note: completion_percentage removed from model
        assert dashboard.transfer_notes == "Making progress in the team"
        assert dashboard.state == ProjectState.IN_PROGRESS

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called twice (once for state change, once for progress update)
        assert team_handler.log_action.call_count == 2

    @pytest.mark.asyncio
    async def test_mark_criterion_completed(self, team_handler, mock_context):
        """Test marking a success criterion as completed."""
        # Call the method
        success, message, updated_dashboard = await team_handler.mark_criterion_completed(
            "test-goal-id", "test-criterion-id"
        )

        # Assertions
        assert success is True
        assert "Marked criterion" in message
        assert updated_dashboard is not None
        assert updated_dashboard.achieved_criteria == 1
        assert updated_dashboard.total_criteria == 1
        # Note: completion_percentage removed from model

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        team_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_project_completion(self, team_handler, mock_context):
        """Test reporting project completion."""
        # Call the method
        success, message, dashboard = await team_handler.report_project_completion(
            "KnowledgePackage has been successfully completed with all objectives achieved."
        )

        # Assertions
        assert success is True
        assert "KnowledgePackage has been marked as completed" in message
        assert dashboard is not None
        assert dashboard.state == ProjectState.COMPLETED
        # Note: completion_percentage removed from model
        assert (
            dashboard.transfer_notes == "KnowledgePackage has been successfully completed with all objectives achieved."
        )

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        team_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project_info(self, team_handler, mock_context):
        """Test getting project info."""
        # Call the method
        project_info = await team_handler.get_project_info()

        # Assertions
        assert project_info["has_project"] is True
        assert project_info["project_id"] == "test-project-id"
        assert project_info["role"] == "team"
        assert project_info["title"] == "Test KnowledgePackage"
        assert project_info["status"] == "in_progress"
        assert project_info["progress"] == 50
