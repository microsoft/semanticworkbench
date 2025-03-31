"""
Tests for the direct mission storage functionality.
"""

import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from datetime import datetime

from assistant.mission_data import (
    FieldRequest,
    LogEntry,
    LogEntryType,
    MissionBriefing,
    MissionGoal,
    MissionLog,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from assistant.mission_storage import (
    MissionRole,
    MissionStorage,
    MissionStorageManager,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import write_model


class TestMissionStorage(unittest.IsolatedAsyncioTestCase):
    """Test the direct mission storage functionality."""

    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_mission_storage"
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)

        # Create test IDs
        self.mission_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"

        # Create mission directory structure
        self.mission_dir = MissionStorageManager.get_mission_dir(self.mission_id)
        self.shared_dir = MissionStorageManager.get_shared_dir(self.mission_id)

        # Set up directories for different conversation roles
        self.hq_dir = self.mission_dir / MissionRole.HQ.value
        self.hq_dir.mkdir(exist_ok=True)

        self.field_dir = self.mission_dir / f"field_{self.conversation_id}"
        self.field_dir.mkdir(exist_ok=True)

        # Set up patching
        self.patches = []

        # Create a mock context
        self.context = unittest.mock.MagicMock()
        self.context.id = self.conversation_id

        # Mock assistant
        mock_assistant = unittest.mock.MagicMock()
        mock_assistant.id = "test-assistant-id"
        self.context.assistant = mock_assistant

        # Patch storage_directory_for_context
        def mock_storage_directory_for_context(context, *args, **kwargs):
            return self.test_dir / f"context_{context.id}"

        patch1 = unittest.mock.patch(
            "assistant.mission_storage.storage_directory_for_context", side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)

        # Create initial test data
        self.create_test_mission_data()

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

    def create_test_mission_data(self):
        """Create test mission data."""
        # Create a mission briefing
        test_goal = MissionGoal(
            name="Test Goal",
            description="This is a test goal",
            success_criteria=[SuccessCriterion(description="Test criterion")],
        )

        briefing = MissionBriefing(
            mission_name="Test Mission",
            mission_description="Test mission description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
            goals=[test_goal],
        )

        # Write briefing to the proper path using MissionStorage
        briefing_path = MissionStorageManager.get_briefing_path(self.mission_id)
        briefing_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(briefing_path, briefing)

        # Create a field request
        request = FieldRequest(
            request_id=str(uuid.uuid4()),
            title="Test Request",
            description="This is a test request",
            priority=RequestPriority.HIGH,
            status=RequestStatus.NEW,  # Use enum value
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write request to the proper path using MissionStorage
        request_path = MissionStorageManager.get_field_request_path(self.mission_id, request.request_id)
        request_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(request_path, request)

        # Create context directories
        context_dir = self.test_dir / f"context_{self.conversation_id}"
        context_dir.mkdir(exist_ok=True, parents=True)

    async def test_read_mission_briefing(self):
        """Test reading a mission briefing."""
        # Read the briefing using MissionStorage
        briefing = MissionStorage.read_mission_briefing(self.mission_id)

        # Verify the briefing was loaded correctly
        self.assertIsNotNone(briefing, "Should load the briefing")
        if briefing:  # Type checking guard
            self.assertEqual(briefing.mission_name, "Test Mission")
            self.assertEqual(briefing.mission_description, "Test mission description")
            self.assertEqual(len(briefing.goals), 1)
            self.assertEqual(briefing.goals[0].name, "Test Goal")

    async def test_read_field_request(self):
        """Test reading a field request."""
        # First get all requests to find the request ID
        requests = MissionStorage.get_all_field_requests(self.mission_id)
        self.assertEqual(len(requests), 1, "Should find one request")
        request_id = requests[0].request_id

        # Read the request using MissionStorage
        request = MissionStorage.read_field_request(self.mission_id, request_id)

        # Verify the request was loaded correctly
        self.assertIsNotNone(request, "Should load the request")
        if request:  # Type checking guard
            self.assertEqual(request.title, "Test Request")
            self.assertEqual(request.description, "This is a test request")
            self.assertEqual(request.priority, RequestPriority.HIGH)

    async def test_write_mission_log(self):
        """Test writing a mission log."""
        # Create a log entry and proper LogEntry objects
        log_entry = MissionLog(
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
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write the log
        MissionStorage.write_mission_log(self.mission_id, log_entry)

        # Read the log back
        log = MissionStorage.read_mission_log(self.mission_id)

        # Verify the log was saved and loaded correctly
        self.assertIsNotNone(log, "Should load the log")
        if log:  # Type checking guard
            self.assertEqual(len(log.entries), 1)
            self.assertEqual(log.entries[0].entry_type, LogEntryType.INFORMATION_UPDATE)
            self.assertEqual(log.entries[0].message, "Test log entry")

    async def test_mission_directory_structure(self):
        """Test the mission directory structure."""
        # Verify mission directory exists
        self.assertTrue(self.mission_dir.exists(), "Mission directory should exist")

        # Verify shared directory exists
        self.assertTrue(self.shared_dir.exists(), "Shared directory should exist")

        # Verify HQ directory exists
        self.assertTrue(self.hq_dir.exists(), "HQ directory should exist")

        # Verify field directory exists
        self.assertTrue(self.field_dir.exists(), "Field directory should exist")


if __name__ == "__main__":
    unittest.main()
