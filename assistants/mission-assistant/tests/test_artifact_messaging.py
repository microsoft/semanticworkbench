import shutil
import pathlib
import unittest
import unittest.mock
import uuid

from assistant.artifacts import (
    ArtifactType,
    MissionBriefing,
    RequestPriority,
)
from assistant.artifact_messaging import ArtifactManager, ArtifactMessenger
from assistant.mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorageManager,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import ConversationContext


class TestArtifactMessaging(unittest.IsolatedAsyncioTestCase):
    """Test the updated artifact messaging system with the new storage structure."""
    
    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_artifacts"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)
        
        # Create test mission and conversation IDs
        self.mission_id = str(uuid.uuid4())
        self.hq_conversation_id = str(uuid.uuid4())
        self.field_conversation_id = str(uuid.uuid4())
        
        # Set up mock contexts
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
        
        # Patch storage_directory_for_context to return predictable paths
        def mock_storage_directory_for_context(context, *args, **kwargs):
            if context.id == self.hq_conversation_id:
                return self.test_dir / f"hq_context_{context.id}"
            else:
                return self.test_dir / f"field_context_{context.id}"
        
        patch1 = unittest.mock.patch(
            "assistant.mission_storage.storage_directory_for_context",
            side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)
        
        # Patch ConversationMissionManager.get_conversation_mission
        async def mock_get_conversation_mission(context):
            return self.mission_id
            
        patch2 = unittest.mock.patch.object(
            ConversationMissionManager,
            "get_conversation_mission",
            side_effect=mock_get_conversation_mission
        )
        self.mock_get_mission = patch2.start()
        self.patches.append(patch2)
        
        # Patch ConversationMissionManager.get_conversation_role
        async def mock_get_conversation_role(context):
            if context.id == self.hq_conversation_id:
                return MissionRole.HQ
            else:
                return MissionRole.FIELD
                
        patch3 = unittest.mock.patch.object(
            ConversationMissionManager,
            "get_conversation_role", 
            side_effect=mock_get_conversation_role
        )
        self.mock_get_role = patch3.start()
        self.patches.append(patch3)
        
        # Create mission directory structure
        MissionStorageManager.get_mission_dir(self.mission_id)
        MissionStorageManager.get_conversation_dir(self.mission_id, self.hq_conversation_id, MissionRole.HQ)
        MissionStorageManager.get_conversation_dir(self.mission_id, self.field_conversation_id, MissionRole.FIELD)
        MissionStorageManager.get_shared_dir(self.mission_id)
        MissionStorageManager.get_artifact_dir(self.mission_id, ArtifactType.MISSION_BRIEFING.value)
        
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
    
    async def test_save_and_load_mission_briefing(self):
        """Test saving and loading a mission briefing artifact."""
        # Create a test mission briefing
        mission_briefing = MissionBriefing(
            artifact_id=str(uuid.uuid4()),
            mission_name="Test Mission",
            mission_description="This is a test mission",
            created_by="test-user-id",
            updated_by="test-user-id",
            conversation_id=self.hq_conversation_id,
        )
        
        # Save the briefing using ArtifactMessenger
        save_result = await ArtifactMessenger.save_artifact(self.hq_context, mission_briefing)
        self.assertTrue(save_result, "Should successfully save the briefing")
        
        # Load the briefing using ArtifactMessenger
        loaded_briefing = await ArtifactMessenger.load_artifact(
            self.field_context, mission_briefing.artifact_id, MissionBriefing
        )
        
        # Verify the loaded briefing
        self.assertIsNotNone(loaded_briefing, "Should load the briefing")
        if loaded_briefing:  # Type guard for static analysis
            self.assertEqual(loaded_briefing.artifact_id, mission_briefing.artifact_id)
            self.assertEqual(loaded_briefing.mission_name, "Test Mission")
            self.assertEqual(loaded_briefing.mission_description, "This is a test mission")
    
    async def test_get_artifacts_by_type(self):
        """Test retrieving all artifacts of a specific type."""
        # Create multiple briefings
        briefing_ids = []
        for i in range(3):
            briefing = MissionBriefing(
                artifact_id=str(uuid.uuid4()),
                mission_name=f"Test Mission {i}",
                mission_description=f"Description {i}",
                created_by="test-user-id",
                updated_by="test-user-id",
                conversation_id=self.hq_conversation_id,
            )
            briefing_ids.append(briefing.artifact_id)
            # Save each briefing
            await ArtifactMessenger.save_artifact(self.hq_context, briefing)
        
        # Retrieve all briefings
        briefings = await ArtifactMessenger.get_artifacts_by_type(self.hq_context, MissionBriefing)
        
        # Verify we got all briefings
        self.assertEqual(len(briefings), 3, "Should retrieve all three briefings")
        retrieved_ids = [b.artifact_id for b in briefings]
        for briefing_id in briefing_ids:
            self.assertIn(briefing_id, retrieved_ids, f"Briefing {briefing_id} should be in results")
    
    async def test_artifact_manager_create_mission_briefing(self):
        """Test creating a mission briefing via ArtifactManager."""
        # Mock the get_participants method to return a user
        participant = unittest.mock.MagicMock()
        participant.id = "test-user-id"
        participant.role = "user"
        participant.name = "Test User"  # Add a string name
        participants_response = unittest.mock.MagicMock()
        participants_response.participants = [participant]
        self.hq_context.get_participants = unittest.mock.AsyncMock(return_value=participants_response)
        
        # Create the mission briefing
        success, briefing = await ArtifactManager.create_mission_briefing(
            self.hq_context,
            mission_name="Manager Created Mission",
            mission_description="Created via ArtifactManager",
            goals=[
                {
                    "name": "Test Goal",
                    "description": "A test goal",
                    "priority": 1,
                    "success_criteria": ["Criterion 1", "Criterion 2"]
                }
            ]
        )
        
        # Verify creation was successful
        self.assertTrue(success, "Mission briefing creation should succeed")
        self.assertIsNotNone(briefing, "Should return the created briefing")
        
        if briefing:  # Type guard for static analysis
            # Load the briefing to verify it was saved
            loaded_briefing = await ArtifactMessenger.load_artifact(
                self.field_context, briefing.artifact_id, MissionBriefing
            )
            
            self.assertIsNotNone(loaded_briefing, "Should be able to load the created briefing")
            if loaded_briefing:  # Type guard
                self.assertEqual(loaded_briefing.mission_name, "Manager Created Mission")
                self.assertEqual(len(loaded_briefing.goals), 1, "Should have one goal")
                self.assertEqual(loaded_briefing.goals[0].name, "Test Goal")
                self.assertEqual(len(loaded_briefing.goals[0].success_criteria), 2, "Should have two criteria")
    
    async def test_create_and_resolve_field_request(self):
        """Test the field request creation and resolution process."""
        # Mock the get_participants method to return a user
        participant = unittest.mock.MagicMock()
        participant.id = "field-user-id"
        participant.role = "user"
        participant.name = "Field User"  # Add a string name
        participants_response = unittest.mock.MagicMock()
        participants_response.participants = [participant]
        self.field_context.get_participants = unittest.mock.AsyncMock(return_value=participants_response)
        
        # Create a field request
        success, request = await ArtifactManager.create_field_request(
            self.field_context,
            title="Need Information",
            description="I need more details about the mission objective",
            priority=RequestPriority.HIGH
        )
        
        # Verify creation was successful
        self.assertTrue(success, "Field request creation should succeed")
        self.assertIsNotNone(request, "Should return the created request")
        
        # Now resolve the request from HQ
        hq_participant = unittest.mock.MagicMock()
        hq_participant.id = "hq-user-id"
        hq_participant.role = "user"
        hq_participant.name = "HQ User"  # Add a string name
        hq_participants_response = unittest.mock.MagicMock()
        hq_participants_response.participants = [hq_participant]
        self.hq_context.get_participants = unittest.mock.AsyncMock(return_value=hq_participants_response)
        
        # Patch log_artifact_update to simplify the test
        patch_log = unittest.mock.patch.object(
            ArtifactMessenger,
            "log_artifact_update",
            return_value=None
        )
        self.mock_log_artifact = patch_log.start()
        self.patches.append(patch_log)
        
        # Patch the send_messages method on the context client to prevent actual API calls
        self.hq_context._workbench_client = unittest.mock.MagicMock()
        self.hq_context._workbench_client.send_messages = unittest.mock.AsyncMock(return_value=None)
        
        # Patch the get_conversation_client method to return a mock client
        from assistant.mission import ConversationClientManager
        mock_target_client = unittest.mock.MagicMock()
        mock_target_client.send_messages = unittest.mock.AsyncMock(return_value=None)
        
        patch = unittest.mock.patch.object(
            ConversationClientManager,
            "get_conversation_client",
            return_value=mock_target_client
        )
        self.mock_client = patch.start()
        self.patches.append(patch)
        
        if request:  # Type guard
            # Resolve the request
            resolve_success, resolved_request = await ArtifactManager.resolve_field_request(
                self.hq_context,
                request.artifact_id,
                "Here are the details you requested: [mission objective details]"
            )
            
            # Verify resolution was successful
            self.assertTrue(resolve_success, "Field request resolution should succeed")
            self.assertIsNotNone(resolved_request, "Should return the resolved request")
            
            if resolved_request:  # Type guard
                self.assertEqual(resolved_request.status, "resolved", "Request status should be resolved")
                self.assertIsNotNone(resolved_request.resolution, "Resolution should be set")
                self.assertEqual(
                    resolved_request.resolution,
                    "Here are the details you requested: [mission objective details]"
                )


if __name__ == "__main__":
    unittest.main()