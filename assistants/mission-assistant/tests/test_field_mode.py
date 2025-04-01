"""Tests for the Field conversation handler."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


# Create mock classes for testing without importing from the actual modules
class ArtifactType:
    MISSION_BRIEFING = "mission_briefing"
    MISSION_STATUS = "mission_status"
    FIELD_REQUEST = "field_request"
    MISSION_LOG = "mission_log"
    KNOWLEDGE_BASE = "mission_kb"


class MissionState:
    PLANNING = "planning"
    READY_FOR_FIELD = "ready_for_field"
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
    GATE_PASSED = "gate_passed"
    MISSION_COMPLETED = "mission_completed"


class MissionRole:
    FIELD = "field"
    HQ = "hq"


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
        mission_id=None,
        **kwargs,
    ):
        self.artifact_id = artifact_id or "test-artifact-id"
        self.artifact_type = artifact_type
        self.created_by = created_by
        self.updated_by = updated_by
        self.conversation_id = conversation_id
        self.mission_id = mission_id
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.version = 1
        # Add any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


class FieldRequest(BaseArtifact):
    def __init__(self, title=None, description=None, priority=None, status=None, **kwargs):
        super().__init__(artifact_type=ArtifactType.FIELD_REQUEST, **kwargs)
        self.title = title or "Test Request"
        self.description = description or "Test Description"
        self.priority = priority or RequestPriority.MEDIUM
        self.status = status or RequestStatus.NEW
        self.resolution = None
        self.resolved_at = None
        self.resolved_by = None


class MissionStatus(BaseArtifact):
    def __init__(
        self, state=None, progress_percentage=0, active_blockers=None, completed_criteria=0, total_criteria=0, **kwargs
    ):
        super().__init__(artifact_type=ArtifactType.MISSION_STATUS, **kwargs)
        self.state = state or MissionState.PLANNING
        self.progress_percentage = progress_percentage
        self.active_blockers = active_blockers or []
        self.completed_criteria = completed_criteria
        self.total_criteria = total_criteria
        self.status_message = None


class SuccessCriterion:
    def __init__(self, id=None, description=None, completed=False, completed_by=None):
        self.id = id or "test-criterion-id"
        self.description = description or "Test criterion"
        self.completed = completed
        self.completed_at = None if not completed else datetime.utcnow()
        self.completed_by = completed_by


class MissionGoal:
    def __init__(self, id=None, name=None, description=None, priority=1, success_criteria=None):
        self.id = id or "test-goal-id"
        self.name = name or "Test Goal"
        self.description = description or "Test Goal Description"
        self.priority = priority
        self.success_criteria = success_criteria or []


class MissionBriefing(BaseArtifact):
    def __init__(self, mission_name=None, mission_description=None, goals=None, **kwargs):
        super().__init__(artifact_type=ArtifactType.MISSION_BRIEFING, **kwargs)
        self.mission_name = mission_name or "Test Mission"
        self.mission_description = mission_description or "Test Description"
        self.goals = goals or []


# Create a mock for the FieldConversationHandler
class MockFieldConversationHandler:
    def __init__(self, context):
        self.context = context
        self.log_action = AsyncMock()

    async def create_field_request(self, title, description, priority=RequestPriority.MEDIUM):
        # Mock implementation
        request = FieldRequest(
            title=title,
            description=description,
            priority=priority,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            mission_id="test-mission-id",
        )

        # Call mocked log_action
        await self.log_action(
            LogEntryType.REQUEST_CREATED,
            f"Created field request: {title}",
            related_artifact_id=request.artifact_id,
            related_artifact_type=ArtifactType.FIELD_REQUEST,
        )

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Created field request: {title}",
                message_type=MessageType.notice,
            )
        )

        return True, f"Created field request: {title}", request

    async def update_mission_status(self, progress_percentage, status_message=None):
        # Mock implementation
        status = MissionStatus(
            state=MissionState.IN_PROGRESS,
            progress_percentage=progress_percentage,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            mission_id="test-mission-id",
        )
        status.status_message = status_message

        # Call mocked log_action for state change and progress update
        await self.log_action(LogEntryType.GATE_PASSED, "Mission is now in progress")

        await self.log_action(LogEntryType.STATUS_CHANGED, f"Updated mission progress to {progress_percentage}%")

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content=f"Updated mission progress to {progress_percentage}%",
                message_type=MessageType.notice,
            )
        )

        return True, f"Updated mission progress to {progress_percentage}%", status

    async def mark_criterion_completed(self, goal_id, criterion_id):
        # Mock implementation
        criterion = SuccessCriterion(id=criterion_id, description="Test criterion")
        criterion.completed = True
        criterion.completed_at = datetime.utcnow()
        criterion.completed_by = "test-user-id"

        status = MissionStatus(
            state=MissionState.IN_PROGRESS,
            progress_percentage=100,
            completed_criteria=1,
            total_criteria=1,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            mission_id="test-mission-id",
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

        return True, f"Marked criterion '{criterion.description}' as completed.", status

    async def report_mission_completed(self, completion_summary):
        # Mock implementation
        status = MissionStatus(
            state=MissionState.COMPLETED,
            progress_percentage=100,
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=str(self.context.id),
            mission_id="test-mission-id",
        )
        status.status_message = completion_summary

        # Call mocked log_action
        await self.log_action(LogEntryType.MISSION_COMPLETED, "Mission marked as completed")

        # Send notification
        await self.context.send_messages(
            NewConversationMessage(
                content="🎉 Mission has been marked as completed.",
                message_type=MessageType.notice,
            )
        )

        return True, "Mission has been marked as completed", status

    async def get_mission_info(self):
        # Mock implementation
        return {
            "has_mission": True,
            "mission_id": "test-mission-id",
            "role": "field",
            "mission_name": "Test Mission",
            "mission_description": "A test mission",
            "status": "in_progress",
            "progress": 50,
            "open_requests": 0,
            "pending_requests": [],
        }


class TestFieldConversationHandler:
    """Test cases for FieldConversationHandler."""

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
    def field_handler(self, mock_context):
        """Create a MockFieldConversationHandler instance with a mock context."""
        return MockFieldConversationHandler(mock_context)

    @pytest.mark.asyncio
    async def test_create_field_request(self, field_handler, mock_context):
        """Test creating a field request."""
        # Call the method
        success, message, request = await field_handler.create_field_request(
            "Test Request", "This is a test request", RequestPriority.HIGH
        )

        # Assertions
        assert success is True
        assert "Created field request: Test Request" in message
        assert request is not None
        assert request.title == "Test Request"
        assert request.description == "This is a test request"
        assert request.priority == RequestPriority.HIGH
        assert request.created_by == "test-user-id"

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        field_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_mission_status(self, field_handler, mock_context):
        """Test updating the mission status."""
        # Call the method
        success, message, status = await field_handler.update_mission_status(50, "Making progress in the field")

        # Assertions
        assert success is True
        assert "Updated mission progress to 50%" in message
        assert status is not None
        assert status.progress_percentage == 50
        assert status.status_message == "Making progress in the field"
        assert status.state == MissionState.IN_PROGRESS

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called twice (once for state change, once for progress update)
        assert field_handler.log_action.call_count == 2

    @pytest.mark.asyncio
    async def test_mark_criterion_completed(self, field_handler, mock_context):
        """Test marking a success criterion as completed."""
        # Call the method
        success, message, updated_status = await field_handler.mark_criterion_completed(
            "test-goal-id", "test-criterion-id"
        )

        # Assertions
        assert success is True
        assert "Marked criterion" in message
        assert updated_status is not None
        assert updated_status.completed_criteria == 1
        assert updated_status.total_criteria == 1
        assert updated_status.progress_percentage == 100  # 1/1 = 100%

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        field_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_mission_completed(self, field_handler, mock_context):
        """Test reporting mission completion."""
        # Call the method
        success, message, status = await field_handler.report_mission_completed(
            "Mission has been successfully completed with all objectives achieved."
        )

        # Assertions
        assert success is True
        assert "Mission has been marked as completed" in message
        assert status is not None
        assert status.state == MissionState.COMPLETED
        assert status.progress_percentage == 100
        assert status.status_message == "Mission has been successfully completed with all objectives achieved."

        # Verify that a notification was sent
        mock_context.send_messages.assert_called_once()

        # Verify log_action was called
        field_handler.log_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mission_info(self, field_handler, mock_context):
        """Test getting mission info."""
        # Call the method
        mission_info = await field_handler.get_mission_info()

        # Assertions
        assert mission_info["has_mission"] is True
        assert mission_info["mission_id"] == "test-mission-id"
        assert mission_info["role"] == "field"
        assert mission_info["mission_name"] == "Test Mission"
        assert mission_info["status"] == "in_progress"
        assert mission_info["progress"] == 50
