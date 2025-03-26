import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from datetime import datetime

from assistant.mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorageManager,
    MissionStorageReader,
    MissionStorageWriter,
)
from pydantic import BaseModel
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext


class MockArtifact(BaseModel):
    """Mock artifact model for testing."""
    artifact_id: str
    name: str
    content: str
    created_at: str = datetime.utcnow().isoformat()


class TestMissionStorage(unittest.IsolatedAsyncioTestCase):
    """Test the mission storage functionality."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_mission_storage"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)
        
        # Create test mission ID and conversation IDs
        self.mission_id = str(uuid.uuid4())
        self.hq_conversation_id = str(uuid.uuid4())
        self.field_conversation_id = str(uuid.uuid4())
        
        # Set up mock context
        self.mock_assistant = unittest.mock.MagicMock()
        self.mock_assistant.id = "test-assistant-id"
        self.mock_assistant._assistant_service_id = "test-service"
        
        # Create mock HQ context
        self.hq_context = unittest.mock.MagicMock(spec=ConversationContext)
        self.hq_context.id = self.hq_conversation_id
        self.hq_context.assistant = self.mock_assistant
        
        # Create mock Field context
        self.field_context = unittest.mock.MagicMock(spec=ConversationContext)
        self.field_context.id = self.field_conversation_id
        self.field_context.assistant = self.mock_assistant
        
        # Set up patches
        self.patches = []
        
        # Patch storage_directory_for_context to return a predictable path
        
        def mock_storage_directory_for_context(context, *args, **kwargs):
            if context.id == self.hq_conversation_id:
                return self.test_dir / f"hq_context_{context.id}"
            else:
                return self.test_dir / f"field_context_{context.id}"
                
        patch = unittest.mock.patch(
            "assistant.mission_storage.storage_directory_for_context",
            side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch.start()
        self.patches.append(patch)
        
    async def asyncTearDown(self):
        """Clean up after tests."""
        # Restore settings
        settings.storage.root = self.original_storage_root
        
        # Stop all patches
        for patch in self.patches:
            patch.stop()
            
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    async def test_mission_directory_structure(self):
        """Test that the mission directory structure is created correctly."""
        mission_dir = MissionStorageManager.get_mission_dir(self.mission_id)
        
        # Check that the mission directory was created
        self.assertTrue(mission_dir.exists())
        self.assertTrue(mission_dir.is_dir())
        
        # Get conversation directories and verify they're created
        hq_dir = MissionStorageManager.get_conversation_dir(
            self.mission_id, self.hq_conversation_id, MissionRole.HQ
        )
        field_dir = MissionStorageManager.get_conversation_dir(
            self.mission_id, self.field_conversation_id, MissionRole.FIELD
        )
        
        self.assertTrue(hq_dir.exists())
        self.assertTrue(field_dir.exists())
        
        # Check that the shared directory is created
        shared_dir = MissionStorageManager.get_shared_dir(self.mission_id)
        self.assertTrue(shared_dir.exists())
        
        # Check that we can create artifact directories
        for artifact_type in ["briefing", "kb", "requests", "log"]:
            artifact_dir = MissionStorageManager.get_artifact_dir(self.mission_id, artifact_type)
            self.assertTrue(artifact_dir.exists())
            
    async def test_artifact_read_write(self):
        """Test reading and writing artifacts."""
        # Create a test artifact
        artifact_id = str(uuid.uuid4())
        artifact = MockArtifact(
            artifact_id=artifact_id,
            name="Test Artifact",
            content="This is test content"
        )
        
        # Write the artifact to storage
        artifact_path = MissionStorageWriter.write_artifact(
            self.mission_id, "test_artifacts", artifact_id, artifact
        )
        
        # Check that the file was created
        self.assertTrue(artifact_path.exists())
        
        # Read the artifact back
        read_artifact = MissionStorageReader.read_artifact(
            self.mission_id, "test_artifacts", artifact_id, MockArtifact
        )
        
        # Verify that the artifact was read correctly
        self.assertIsNotNone(read_artifact)
        if read_artifact:  # Add type guard for static analysis
            self.assertEqual(read_artifact.artifact_id, artifact_id)
            self.assertEqual(read_artifact.name, "Test Artifact")
            self.assertEqual(read_artifact.content, "This is test content")
        
        # Delete the artifact
        deleted = MissionStorageWriter.delete_artifact(
            self.mission_id, "test_artifacts", artifact_id
        )
        
        # Verify deletion
        self.assertTrue(deleted)
        self.assertFalse(artifact_path.exists())
        
    async def test_read_all_artifacts(self):
        """Test reading all artifacts of a type."""
        # Create multiple test artifacts
        artifacts = []
        for i in range(3):
            artifact_id = str(uuid.uuid4())
            artifact = MockArtifact(
                artifact_id=artifact_id,
                name=f"Test Artifact {i}",
                content=f"Content {i}"
            )
            artifacts.append(artifact)
            MissionStorageWriter.write_artifact(
                self.mission_id, "multi_test", artifact_id, artifact
            )
        
        # Read all artifacts
        read_artifacts = MissionStorageReader.read_all_artifacts(
            self.mission_id, "multi_test", MockArtifact
        )
        
        # Verify the count matches
        self.assertEqual(len(read_artifacts), 3)
        
        # Verify all artifacts were read correctly
        artifact_names = {a.name for a in read_artifacts}
        expected_names = {f"Test Artifact {i}" for i in range(3)}
        self.assertEqual(artifact_names, expected_names)
        
    async def test_conversation_mission_association(self):
        """Test associating a conversation with a mission."""
        # Associate a conversation with a mission
        await ConversationMissionManager.set_conversation_mission(
            self.hq_context, self.mission_id
        )
        
        # Get the mission ID
        mission_id = await ConversationMissionManager.get_conversation_mission(
            self.hq_context
        )
        
        # Verify the mission ID
        self.assertEqual(mission_id, self.mission_id)
        
    async def test_conversation_role(self):
        """Test setting and getting a conversation's role."""
        # Set the conversation role
        await ConversationMissionManager.set_conversation_role(
            self.hq_context, self.mission_id, MissionRole.HQ
        )
        
        # Get the role
        role = await ConversationMissionManager.get_conversation_role(
            self.hq_context
        )
        
        # Verify the role
        self.assertEqual(role, MissionRole.HQ)
        
        # Set a different role
        await ConversationMissionManager.set_conversation_role(
            self.field_context, self.mission_id, MissionRole.FIELD
        )
        
        # Get the role
        role = await ConversationMissionManager.get_conversation_role(
            self.field_context
        )
        
        # Verify the role
        self.assertEqual(role, MissionRole.FIELD)


if __name__ == "__main__":
    unittest.main()