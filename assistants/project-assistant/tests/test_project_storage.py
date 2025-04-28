"""
Tests for the direct project storage functionality.
"""

import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from datetime import datetime

from assistant.project_data import (
    InformationRequest,
    LogEntry,
    LogEntryType,
    ProjectBrief,
    ProjectGoal,
    ProjectInfo,
    ProjectLog,
    ProjectWhiteboard,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from assistant.project_storage import (
    ConversationProjectManager,
    ConversationRole,
    CoordinatorConversationMessage,
    CoordinatorConversationStorage,
    ProjectStorage,
    ProjectStorageManager,
)
from semantic_workbench_api_model.workbench_model import AssistantStateEvent
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import write_model


class TestProjectStorage(unittest.IsolatedAsyncioTestCase):
    """Test the direct project storage functionality."""

    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_project_storage"
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)

        # Create test IDs
        self.project_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"

        # Create project directory structure
        self.project_dir = ProjectStorageManager.get_project_dir(self.project_id)

        # Set up directories for different conversation roles
        self.coordinator_dir = self.project_dir / ConversationRole.COORDINATOR.value
        self.coordinator_dir.mkdir(exist_ok=True)

        self.team_dir = self.project_dir / f"team_{self.conversation_id}"
        self.team_dir.mkdir(exist_ok=True)

        # Set up patching
        self.patches = []

        # Create a mock context
        self.context = unittest.mock.MagicMock()
        self.context.id = self.conversation_id

        # Mock assistant
        mock_assistant = unittest.mock.MagicMock()
        mock_assistant.id = "test-assistant-id"
        self.context.assistant = mock_assistant

        # Mock send_conversation_state_event
        self.context.send_conversation_state_event = unittest.mock.AsyncMock()

        # Patch storage_directory_for_context
        def mock_storage_directory_for_context(context, *args, **kwargs):
            return self.test_dir / f"context_{context.id}"

        patch1 = unittest.mock.patch(
            "assistant.project_storage.storage_directory_for_context", side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)

        # Create initial test data
        self.create_test_project_data()

        return None

    async def asyncTearDown(self):
        """Clean up test environment."""
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Restore settings
        settings.storage.root = self.original_storage_root

        # Stop all patches
        for patch in self.patches:
            patch.stop()

    def create_test_project_data(self):
        """Create test project data."""
        # Create a project brief
        test_goal = ProjectGoal(
            name="Test Goal",
            description="This is a test goal",
            success_criteria=[SuccessCriterion(description="Test criterion")],
        )

        brief = ProjectBrief(
            project_name="Test Project",
            project_description="Test project description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
            goals=[test_goal],
        )

        # Write brief to the proper path using ProjectStorage
        brief_path = ProjectStorageManager.get_brief_path(self.project_id)
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(brief_path, brief)

        # Create project info
        project_info = ProjectInfo(
            project_id=self.project_id,
            coordinator_conversation_id=self.conversation_id,
        )
        project_info_path = ProjectStorageManager.get_project_info_path(self.project_id)
        write_model(project_info_path, project_info)

        # Create an information request
        request = InformationRequest(
            request_id=str(uuid.uuid4()),
            title="Test Request",
            description="This is a test request",
            priority=RequestPriority.HIGH,
            status=RequestStatus.NEW,  # Use enum value
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write request to the proper path using ProjectStorage
        request_path = ProjectStorageManager.get_information_request_path(self.project_id, request.request_id)
        request_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(request_path, request)

        # Create context directories
        context_dir = self.test_dir / f"context_{self.conversation_id}"
        context_dir.mkdir(exist_ok=True, parents=True)

    async def test_read_project_brief(self):
        """Test reading a project brief."""
        # Read the brief using ProjectStorage
        brief = ProjectStorage.read_project_brief(self.project_id)

        # Verify the brief was loaded correctly
        self.assertIsNotNone(brief, "Should load the brief")
        if brief:  # Type checking guard
            self.assertEqual(brief.project_name, "Test Project")
            self.assertEqual(brief.project_description, "Test project description")
            self.assertEqual(len(brief.goals), 1)
            self.assertEqual(brief.goals[0].name, "Test Goal")

    async def test_read_information_request(self):
        """Test reading an information request."""
        # First get all requests to find the request ID
        requests = ProjectStorage.get_all_information_requests(self.project_id)
        self.assertEqual(len(requests), 1, "Should find one request")
        request_id = requests[0].request_id

        # Read the request using ProjectStorage
        request = ProjectStorage.read_information_request(self.project_id, request_id)

        # Verify the request was loaded correctly
        self.assertIsNotNone(request, "Should load the request")
        if request:  # Type checking guard
            self.assertEqual(request.title, "Test Request")
            self.assertEqual(request.description, "This is a test request")
            self.assertEqual(request.priority, RequestPriority.HIGH)

    async def test_write_project_log(self):
        """Test writing a project log."""
        # Create a log entry and proper LogEntry objects
        log_entry = ProjectLog(
            entries=[
                LogEntry(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    entry_type=LogEntryType.INFORMATION_UPDATE,
                    message="Test log entry",
                    user_id=self.user_id,
                    user_name="Test User",
                )
            ],
        )

        # Write the log
        ProjectStorage.write_project_log(self.project_id, log_entry)

        # Read the log back
        log = ProjectStorage.read_project_log(self.project_id)

        # Verify the log was saved and loaded correctly
        self.assertIsNotNone(log, "Should load the log")
        if log:  # Type checking guard
            self.assertEqual(len(log.entries), 1)
            self.assertEqual(log.entries[0].entry_type, LogEntryType.INFORMATION_UPDATE)
            self.assertEqual(log.entries[0].message, "Test log entry")

    async def test_project_directory_structure(self):
        """Test the project directory structure."""
        # Verify project directory exists
        self.assertTrue(self.project_dir.exists(), "Project directory should exist")

        # Verify Coordinator directory exists
        self.assertTrue(self.coordinator_dir.exists(), "Coordinator directory should exist")

        # Verify team directory exists
        self.assertTrue(self.team_dir.exists(), "Team directory should exist")

    async def test_coordinator_conversation_storage(self):
        """Test the coordinator conversation storage functionality."""
        # Create coordinator conversation storage
        messages = [
            CoordinatorConversationMessage(
                message_id=str(uuid.uuid4()),
                content="Test message 1",
                sender_name="Test User",
                is_assistant=False,
            ),
            CoordinatorConversationMessage(
                message_id=str(uuid.uuid4()),
                content="Test message 2",
                sender_name="Test Assistant",
                is_assistant=True,
            ),
        ]

        conv_storage = CoordinatorConversationStorage(
            project_id=self.project_id,
            messages=messages,
        )

        # Write to storage
        ProjectStorage.write_coordinator_conversation(self.project_id, conv_storage)

        # Read back
        read_storage = ProjectStorage.read_coordinator_conversation(self.project_id)

        # Verify data was saved correctly
        self.assertIsNotNone(read_storage, "Should load the coordinator conversation")
        if read_storage:
            self.assertEqual(read_storage.project_id, self.project_id)
            self.assertEqual(len(read_storage.messages), 2)
            self.assertEqual(read_storage.messages[0].content, "Test message 1")
            self.assertEqual(read_storage.messages[1].content, "Test message 2")
            self.assertFalse(read_storage.messages[0].is_assistant)
            self.assertTrue(read_storage.messages[1].is_assistant)

    async def test_append_coordinator_message(self):
        """Test appending a message to coordinator conversation storage."""
        # Start with empty storage
        ProjectStorage.append_coordinator_message(
            project_id=self.project_id,
            message_id=str(uuid.uuid4()),
            content="First message",
            sender_name="Test User",
        )

        # Append another message
        ProjectStorage.append_coordinator_message(
            project_id=self.project_id,
            message_id=str(uuid.uuid4()),
            content="Second message",
            sender_name="Test Assistant",
            is_assistant=True,
        )

        # Read back
        storage = ProjectStorage.read_coordinator_conversation(self.project_id)

        # Verify messages were added
        self.assertIsNotNone(storage, "Should create and load the coordinator conversation")
        if storage:
            self.assertEqual(len(storage.messages), 2)
            self.assertEqual(storage.messages[0].content, "First message")
            self.assertEqual(storage.messages[1].content, "Second message")
            self.assertFalse(storage.messages[0].is_assistant)
            self.assertTrue(storage.messages[1].is_assistant)

    async def test_message_limit_in_coordinator_conversation(self):
        """Test that coordinator conversation storage limits to the most recent messages."""
        # Add more than 50 messages
        for i in range(60):
            ProjectStorage.append_coordinator_message(
                project_id=self.project_id,
                message_id=str(uuid.uuid4()),
                content=f"Message {i + 1}",
                sender_name="Test User",
            )

        # Read back
        storage = ProjectStorage.read_coordinator_conversation(self.project_id)

        # Verify only the most recent 50 messages are kept
        self.assertIsNotNone(storage, "Should load the coordinator conversation")
        if storage:
            self.assertEqual(len(storage.messages), 50, "Should limit to 50 messages")
            # First message should be the 11th message (since we keep the last 50 of 60)
            self.assertEqual(storage.messages[0].content, "Message 11")
            # Last message should be the 60th message
            self.assertEqual(storage.messages[49].content, "Message 60")

    async def test_project_whiteboard(self):
        """Test reading and writing project whiteboard."""
        # Create whiteboard
        whiteboard = ProjectWhiteboard(
            content="# Test Whiteboard\n\nThis is a test whiteboard.",
            is_auto_generated=True,
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write whiteboard
        ProjectStorage.write_project_whiteboard(self.project_id, whiteboard)

        # Read whiteboard
        read_whiteboard = ProjectStorage.read_project_whiteboard(self.project_id)

        # Verify whiteboard was saved correctly
        self.assertIsNotNone(read_whiteboard, "Should load the whiteboard")
        if read_whiteboard:
            self.assertEqual(read_whiteboard.content, "# Test Whiteboard\n\nThis is a test whiteboard.")
            self.assertTrue(read_whiteboard.is_auto_generated)

    async def test_refresh_current_ui(self):
        """Test refreshing the current UI inspector."""
        # Call refresh_current_ui
        await ProjectStorage.refresh_current_ui(self.context)

        # Verify that send_conversation_state_event was called with correct parameters
        self.context.send_conversation_state_event.assert_called_once()
        called_event = self.context.send_conversation_state_event.call_args[0][0]
        self.assertIsInstance(called_event, AssistantStateEvent)
        self.assertEqual(called_event.state_id, "project_status")
        self.assertEqual(called_event.event, "updated")
        self.assertIsNone(called_event.state)

    async def test_project_info(self):
        """Test reading and writing project info."""
        # Read existing project info
        project_info = ProjectStorage.read_project_info(self.project_id)

        # Verify it was loaded correctly
        self.assertIsNotNone(project_info, "Should load project info")
        if project_info:
            self.assertEqual(project_info.project_id, self.project_id)
            self.assertEqual(project_info.coordinator_conversation_id, self.conversation_id)

        # Update project info
        if project_info:
            project_info.status_message = "Test status message"
            project_info.progress_percentage = 50
            project_info.next_actions = ["Action 1", "Action 2"]

            # Write updated project info
            ProjectStorage.write_project_info(self.project_id, project_info)

            # Read updated project info
            updated_info = ProjectStorage.read_project_info(self.project_id)

            # Verify updates were saved
            self.assertIsNotNone(updated_info, "Should load updated project info")
            if updated_info:
                self.assertEqual(updated_info.status_message, "Test status message")
                self.assertEqual(updated_info.progress_percentage, 50)
                self.assertEqual(updated_info.next_actions, ["Action 1", "Action 2"])

    async def test_get_linked_conversations_dir(self):
        """Test getting linked conversations directory."""
        # Get linked conversations directory
        linked_dir = ProjectStorageManager.get_linked_conversations_dir(self.project_id)

        # Verify directory exists
        self.assertTrue(linked_dir.exists(), "Linked conversations directory should exist")
        self.assertEqual(linked_dir.name, "linked_conversations")

    async def test_conversation_association(self):
        """Test conversation association with project."""
        # Mock ConversationProjectManager.associate_conversation_with_project
        with unittest.mock.patch("assistant.project_storage.write_model") as mock_write_model:
            # Mock conversation project path
            conversation_project_file = ProjectStorageManager.get_conversation_project_file_path(self.context)

            # Call associate_conversation_with_project
            await ConversationProjectManager.associate_conversation_with_project(self.context, self.project_id)

            # Verify write_model was called
            mock_write_model.assert_called_once()

            # Verify the file path in the call
            call_args = mock_write_model.call_args[0]
            self.assertEqual(call_args[0], conversation_project_file)

            # Verify the ProjectAssociation object created
            self.assertEqual(call_args[1].project_id, self.project_id)

    async def test_log_project_event(self):
        """Test logging a project event."""

        # Create mock for get_current_user
        async def mock_get_current_user_impl(*args, **kwargs):
            return "test-user", "Test User"

        # Patch get_current_user with our async mock implementation
        with unittest.mock.patch("assistant.project_storage.get_current_user", side_effect=mock_get_current_user_impl):
            # Call log_project_event
            success = await ProjectStorage.log_project_event(
                context=self.context,
                project_id=self.project_id,
                entry_type=LogEntryType.INFORMATION_UPDATE.value,
                message="Test event log",
                related_entity_id="test-entity-id",
                metadata={"test": "metadata"},
            )

            # Verify success
            self.assertTrue(success, "Should log event successfully")

            # Read log to verify entry was added
            log = ProjectStorage.read_project_log(self.project_id)
            self.assertIsNotNone(log, "Should create and load log")
            if log:
                # If log already had entries from setup, this should find the new one
                found_entry = False
                for entry in log.entries:
                    if entry.message == "Test event log":
                        found_entry = True
                        self.assertEqual(entry.entry_type, LogEntryType.INFORMATION_UPDATE)
                        self.assertEqual(entry.user_id, "test-user")
                        self.assertEqual(entry.user_name, "Test User")
                        self.assertEqual(entry.related_entity_id, "test-entity-id")
                        self.assertEqual(entry.metadata, {"test": "metadata"})
                self.assertTrue(found_entry, "Should find the added log entry")


if __name__ == "__main__":
    unittest.main()
