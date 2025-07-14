"""
Tests for the direct project storage functionality.
"""

import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from datetime import datetime

from assistant.conversation_share_link import ConversationKnowledgePackageManager
from assistant.data import (
    InformationRequest,
    KnowledgeBrief,
    KnowledgeDigest,
    KnowledgePackage,
    KnowledgePackageLog,
    LearningObjective,
    LearningOutcome,
    LogEntry,
    LogEntryType,
    RequestPriority,
    RequestStatus,
)
from assistant.notifications import refresh_current_ui
from assistant.storage import ShareStorage, ShareStorageManager
from assistant.storage_models import (
    ConversationRole,
    CoordinatorConversationMessage,
    CoordinatorConversationStorage,
)
from semantic_workbench_api_model.workbench_model import AssistantStateEvent
from semantic_workbench_assistant import settings


class TestShareStorage(unittest.IsolatedAsyncioTestCase):
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
        self.share_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"

        # Create project directory structure
        self.project_dir = ShareStorageManager.get_share_dir(self.share_id)

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

        # Mock get_participants with the correct structure
        participants_mock = unittest.mock.MagicMock()
        participants_mock.participants = []
        self.context.get_participants = unittest.mock.AsyncMock(return_value=participants_mock)

        # Patch storage_directory_for_context
        def mock_storage_directory_for_context(context, *args, **kwargs):
            return self.test_dir / f"context_{context.id}"

        patch1 = unittest.mock.patch(
            "assistant.storage.storage_directory_for_context", side_effect=mock_storage_directory_for_context
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
        test_goal = LearningObjective(
            name="Test Goal",
            description="This is a test goal",
            learning_outcomes=[LearningOutcome(description="Test criterion")],
        )

        brief = KnowledgeBrief(
            title="Test KnowledgePackage",
            content="Test project description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Create a KnowledgePackage with the goal and brief
        project = KnowledgePackage(
            share_id=self.share_id,
            coordinator_conversation_id=self.conversation_id,
            brief=brief,
            learning_objectives=[test_goal],
            digest=None,
        )

        # Write the project to storage (this now includes the brief and learning objectives)
        ShareStorage.write_share(self.share_id, project)

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

        # Write request using ShareStorage (this will add it to the main share file)
        ShareStorage.write_information_request(self.share_id, request)

        # Create context directories
        context_dir = self.test_dir / f"context_{self.conversation_id}"
        context_dir.mkdir(exist_ok=True, parents=True)

    async def test_read_project_brief(self):
        """Test reading a project brief."""
        # Read the brief using ShareStorage
        brief = ShareStorage.read_knowledge_brief(self.share_id)
        project = ShareStorage.read_share(self.share_id)

        # Verify the brief was loaded correctly
        self.assertIsNotNone(brief, "Should load the brief")
        if brief:  # Type checking guard
            self.assertEqual(brief.title, "Test KnowledgePackage")
            self.assertEqual(brief.content, "Test project description")

        # Verify the project was loaded with goals correctly
        self.assertIsNotNone(project, "Should load the project")
        if project:  # Type checking guard
            self.assertEqual(len(project.learning_objectives), 1)
            self.assertEqual(project.learning_objectives[0].name, "Test Goal")

    async def test_read_information_request(self):
        """Test reading an information request."""
        # First get all requests to find the request ID
        requests = ShareStorage.get_all_information_requests(self.share_id)
        self.assertEqual(len(requests), 1, "Should find one request")
        request_id = requests[0].request_id

        # Read the request using ShareStorage
        request = ShareStorage.read_information_request(self.share_id, request_id)

        # Verify the request was loaded correctly
        self.assertIsNotNone(request, "Should load the request")
        if request:  # Type checking guard
            self.assertEqual(request.title, "Test Request")
            self.assertEqual(request.description, "This is a test request")
            self.assertEqual(request.priority, RequestPriority.HIGH)

    async def test_write_project_log(self):
        """Test writing a project log."""
        # Create a log entry and proper LogEntry objects
        log_entry = KnowledgePackageLog(
            entries=[
                LogEntry(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    entry_type=LogEntryType.SHARE_INFORMATION_UPDATE,
                    message="Test log entry",
                    user_id=self.user_id,
                    user_name="Test User",
                )
            ],
        )

        # Write the log
        ShareStorage.write_share_log(self.share_id, log_entry)

        # Read the log back
        log = ShareStorage.read_share_log(self.share_id)

        # Verify the log was saved and loaded correctly
        self.assertIsNotNone(log, "Should load the log")
        if log:  # Type checking guard
            self.assertEqual(len(log.entries), 1)
            self.assertEqual(log.entries[0].entry_type, LogEntryType.SHARE_INFORMATION_UPDATE)
            self.assertEqual(log.entries[0].message, "Test log entry")

    async def test_project_directory_structure(self):
        """Test the project directory structure."""
        # Verify project directory exists
        self.assertTrue(self.project_dir.exists(), "KnowledgePackage directory should exist")

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
            knowledge_share_id=self.share_id,
            messages=messages,
        )

        # Write to storage
        ShareStorage.write_coordinator_conversation(self.share_id, conv_storage)

        # Read back
        read_storage = ShareStorage.read_coordinator_conversation(self.share_id)

        # Verify data was saved correctly
        self.assertIsNotNone(read_storage, "Should load the coordinator conversation")
        if read_storage:
            self.assertEqual(read_storage.knowledge_share_id, self.share_id)
            self.assertEqual(len(read_storage.messages), 2)
            self.assertEqual(read_storage.messages[0].content, "Test message 1")
            self.assertEqual(read_storage.messages[1].content, "Test message 2")
            self.assertFalse(read_storage.messages[0].is_assistant)
            self.assertTrue(read_storage.messages[1].is_assistant)

    async def test_append_coordinator_message(self):
        """Test appending a message to coordinator conversation storage."""
        # Start with empty storage
        ShareStorage.append_coordinator_message(
            share_id=self.share_id,
            message_id=str(uuid.uuid4()),
            content="First message",
            sender_name="Test User",
        )

        # Append another message
        ShareStorage.append_coordinator_message(
            share_id=self.share_id,
            message_id=str(uuid.uuid4()),
            content="Second message",
            sender_name="Test Assistant",
            is_assistant=True,
        )

        # Read back
        storage = ShareStorage.read_coordinator_conversation(self.share_id)

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
            ShareStorage.append_coordinator_message(
                share_id=self.share_id,
                message_id=str(uuid.uuid4()),
                content=f"Message {i + 1}",
                sender_name="Test User",
            )

        # Read back
        storage = ShareStorage.read_coordinator_conversation(self.share_id)

        # Verify only the most recent 50 messages are kept
        self.assertIsNotNone(storage, "Should load the coordinator conversation")
        if storage:
            self.assertEqual(len(storage.messages), 50, "Should limit to 50 messages")
            # First message should be the 11th message (since we keep the last 50 of 60)
            self.assertEqual(storage.messages[0].content, "Message 11")
            # Last message should be the 60th message
            self.assertEqual(storage.messages[49].content, "Message 60")

    async def test_knowledge_digest(self):
        """Test reading and writing knowledge digest."""
        # Create knowledge digest
        digest = KnowledgeDigest(
            content="# Test Knowledge Digest\n\nThis is a test knowledge digest.",
            is_auto_generated=True,
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write knowledge digest (this will add it to the main share file)
        ShareStorage.write_knowledge_digest(self.share_id, digest)

        # Read knowledge digest
        read_digest = ShareStorage.read_knowledge_digest(self.share_id)

        # Verify knowledge digest was saved correctly
        self.assertIsNotNone(read_digest, "Should load the knowledge digest")
        if read_digest:
            self.assertEqual(read_digest.content, "# Test Knowledge Digest\n\nThis is a test knowledge digest.")
            self.assertTrue(read_digest.is_auto_generated)

    async def test_refresh_current_ui(self):
        """Test refreshing the current UI inspector."""
        # Call refresh_current_ui
        await refresh_current_ui(self.context)

        # Verify that send_conversation_state_event was called 4 times (once per inspector tab)
        self.assertEqual(self.context.send_conversation_state_event.call_count, 4)
        
        # Get all the calls
        calls = self.context.send_conversation_state_event.call_args_list
        expected_state_ids = ["brief", "objectives", "requests", "debug"]
        actual_state_ids = [call[0][0].state_id for call in calls]
        
        # Verify each call has the correct parameters
        for call_args in calls:
            called_event = call_args[0][0]
            self.assertIsInstance(called_event, AssistantStateEvent)
            self.assertEqual(called_event.event, "updated")
            self.assertIsNone(called_event.state)
            self.assertIn(called_event.state_id, expected_state_ids)
        
        # Verify all expected state IDs were called
        self.assertEqual(set(actual_state_ids), set(expected_state_ids))

    async def test_knowledge_package_info(self):
        """Test reading and writing knowledge package info."""
        # Read existing knowledge package
        package = ShareStorage.read_share_info(self.share_id)

        # Verify it was loaded correctly
        self.assertIsNotNone(package, "Should load knowledge package")
        if package:
            self.assertEqual(package.share_id, self.share_id)

            # Update knowledge package info
            package.transfer_notes = "Test status message"
            package.completion_percentage = 50
            package.next_learning_actions = ["Action 1", "Action 2"]

            # Write updated knowledge package
            ShareStorage.write_share_info(self.share_id, package)

            # Read updated knowledge package
            updated_package = ShareStorage.read_share_info(self.share_id)

            # Verify updates were saved
            self.assertIsNotNone(updated_package, "Should load updated knowledge package")
            if updated_package:
                self.assertEqual(updated_package.transfer_notes, "Test status message")
                self.assertEqual(updated_package.completion_percentage, 50)
                self.assertEqual(updated_package.next_learning_actions, ["Action 1", "Action 2"])

    async def test_conversation_tracking_in_json(self):
        """Test that conversations are tracked in JSON instead of file system."""
        # Load knowledge package
        package = ShareStorage.read_share(self.share_id)
        self.assertIsNotNone(package)

        if package:
            # Verify team_conversations dict exists (even if empty)
            self.assertIsInstance(package.team_conversations, dict)

            # Verify helper methods work
            linked_conversations = package.get_all_linked_conversations()
            self.assertIsInstance(linked_conversations, list)

            notification_conversations = package.get_notification_conversations()
            self.assertIsInstance(notification_conversations, list)

    async def test_conversation_association(self):
        """Test conversation association with project."""
        # Mock ConversationKnowledgePackageManager.associate_conversation_with_share
        with unittest.mock.patch("assistant.conversation_share_link.write_model") as mock_write_model:
            # Mock conversation project path
            conversation_project_file = ShareStorageManager.get_conversation_share_file_path(self.context)

            # Call associate_conversation_with_share
            await ConversationKnowledgePackageManager.associate_conversation_with_share(self.context, self.share_id)

            # Verify write_model was called
            mock_write_model.assert_called_once()

            # Verify the file path in the call
            call_args = mock_write_model.call_args[0]
            self.assertEqual(call_args[0], conversation_project_file)

            # Verify the ProjectAssociation object created
            self.assertEqual(call_args[1].share_id, self.share_id)

    async def test_log_project_event(self):
        """Test logging a project event."""

        # Create a test log entry directly
        log_entry = LogEntry(
            entry_type=LogEntryType.SHARE_INFORMATION_UPDATE,
            message="Test direct log entry",
            user_id=self.user_id,
            user_name="Test User",
            related_entity_id="test-entity-id",
            metadata={"test": "metadata"},
        )

        # Create a log with the entry
        log = KnowledgePackageLog(entries=[log_entry])

        # Write the log directly
        ShareStorage.write_share_log(self.share_id, log)

        # Read the log back
        read_log = ShareStorage.read_share_log(self.share_id)
        self.assertIsNotNone(read_log, "Should load the log")
        if read_log:
            # Find our test entry
            found_entry = False
            for entry in read_log.entries:
                if entry.message == "Test direct log entry":
                    found_entry = True
                    self.assertEqual(entry.entry_type, LogEntryType.SHARE_INFORMATION_UPDATE)
                    self.assertEqual(entry.user_id, self.user_id)
                    self.assertEqual(entry.user_name, "Test User")
                    self.assertEqual(entry.related_entity_id, "test-entity-id")
                    self.assertEqual(entry.metadata, {"test": "metadata"})
            self.assertTrue(found_entry, "Should find the added log entry")


if __name__ == "__main__":
    unittest.main()
