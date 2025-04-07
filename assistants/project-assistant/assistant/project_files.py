"""
Project files management module.

This module provides functionality for sharing files between Coordinator and Team conversations.
It enables automatic synchronization of files from Coordinator to Team conversations.
"""

import io
import logging
import pathlib
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .project_data import BaseEntity
from .project_storage import (
    ConversationProjectManager,
    ProjectRole,
    ProjectStorageManager,
    ProjectStorage,
    read_model,
    write_model,
)

logger = logging.getLogger(__name__)


class ProjectFile(BaseModel):
    """Metadata for a file shared within a project."""

    file_id: str
    filename: str
    content_type: str
    file_size: int
    created_by: str  # User ID
    created_at: datetime
    updated_at: datetime
    updated_by: str  # User ID
    is_coordinator_file: bool = True  # Whether this file was created by Coordinator


class ProjectFileCollection(BaseEntity):
    """Collection of file metadata for a project."""

    files: List[ProjectFile] = Field(default_factory=list)


class ProjectFileManager:
    """
    Manages shared project files.
    
    Provides functionality for copying files between conversations and maintaining
    a synchronized file repository for each project.
    """

    @staticmethod
    def get_project_files_dir(project_id: str) -> pathlib.Path:
        """
        Gets the directory for project files.
        
        Args:
            project_id: Project ID
            
        Returns:
            Path to the project files directory
        """
        shared_dir = ProjectStorageManager.get_shared_dir(project_id)
        files_dir = shared_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        return files_dir

    @staticmethod
    def get_file_metadata_path(project_id: str) -> pathlib.Path:
        """
        Gets the path to the file metadata JSON.
        
        Args:
            project_id: Project ID
            
        Returns:
            Path to the file metadata JSON
        """
        files_dir = ProjectFileManager.get_project_files_dir(project_id)
        return files_dir / "file_metadata.json"

    @staticmethod
    def get_file_path(project_id: str, filename: str) -> pathlib.Path:
        """
        Gets the path to a specific file in the project.
        
        Args:
            project_id: Project ID
            filename: Filename
            
        Returns:
            Path to the file
        """
        files_dir = ProjectFileManager.get_project_files_dir(project_id)
        return files_dir / filename

    @staticmethod
    def read_file_metadata(project_id: str) -> Optional[ProjectFileCollection]:
        """
        Reads file metadata for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            ProjectFileCollection or None if not found
        """
        path = ProjectFileManager.get_file_metadata_path(project_id)
        return read_model(path, ProjectFileCollection)

    @staticmethod
    def write_file_metadata(project_id: str, metadata: ProjectFileCollection) -> pathlib.Path:
        """
        Writes file metadata for a project.
        
        Args:
            project_id: Project ID
            metadata: ProjectFileCollection to write
            
        Returns:
            Path to the written file
        """
        path = ProjectFileManager.get_file_metadata_path(project_id)
        write_model(path, metadata)
        return path

    @staticmethod
    async def copy_file_to_project_storage(
        context: ConversationContext,
        project_id: str,
        file: workbench_model.File,
        is_coordinator_file: bool = True,
    ) -> bool:
        """
        Copies a file from a conversation to project storage.
        
        Args:
            context: Conversation context
            project_id: Project ID
            file: File metadata
            is_coordinator_file: Whether this file is from a Coordinator
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the file from the conversation
            buffer = io.BytesIO()
            async with context.read_file(file.filename) as reader:
                async for chunk in reader:
                    buffer.write(chunk)
            
            # Reset buffer position
            buffer.seek(0)
            
            # Write the file to project storage
            file_path = ProjectFileManager.get_file_path(project_id, file.filename)
            with open(file_path, "wb") as f:
                f.write(buffer.getvalue())
            
            # Store file metadata
            file_metadata = ProjectFile(
                file_id=str(getattr(file, "id", "")),
                filename=file.filename,
                content_type=file.content_type,
                file_size=file.file_size,
                created_by=file.participant_id,
                created_at=file.created_datetime,
                updated_at=file.updated_datetime,
                updated_by=file.participant_id,
                is_coordinator_file=is_coordinator_file,
            )
            
            # Add to metadata collection
            metadata_path = ProjectFileManager.get_file_metadata_path(project_id)
            metadata = read_model(metadata_path, ProjectFileCollection)
            if not metadata:
                # Create new collection
                metadata = ProjectFileCollection(
                    created_by=file.participant_id,
                    updated_by=file.participant_id,
                    conversation_id=str(context.id),
                    files=[],
                )
            
            # Check if file already exists in collection
            existing_idx = next((i for i, f in enumerate(metadata.files) if f.filename == file.filename), None)
            if existing_idx is not None:
                metadata.files[existing_idx] = file_metadata
            else:
                metadata.files.append(file_metadata)
            
            # Update metadata
            metadata.updated_at = datetime.utcnow()
            metadata.updated_by = file.participant_id
            metadata.version += 1
            
            # Save metadata
            ProjectFileManager.write_file_metadata(project_id, metadata)
            
            return True
            
        except Exception as e:
            logger.exception(f"Error copying file to project storage: {e}")
            return False

    @staticmethod
    async def delete_file_from_project_storage(
        context: ConversationContext, project_id: str, filename: str
    ) -> bool:
        """
        Deletes a file from project storage.
        
        Args:
            context: Conversation context
            project_id: Project ID
            filename: Filename to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the file path
            file_path = ProjectFileManager.get_file_path(project_id, filename)
            if not file_path.exists():
                return True  # File doesn't exist, nothing to delete
            
            # Remove the file
            file_path.unlink()
            
            # Update metadata
            metadata_path = ProjectFileManager.get_file_metadata_path(project_id)
            metadata = read_model(metadata_path, ProjectFileCollection)
            if not metadata:
                return True  # No metadata to update
            
            # Remove the file from metadata
            metadata.files = [f for f in metadata.files if f.filename != filename]
            
            # Update metadata timestamp
            metadata.updated_at = datetime.utcnow()
            
            # Get user ID
            participants = await context.get_participants()
            for participant in participants.participants:
                if participant.role == "user":
                    metadata.updated_by = participant.id
                    break
            
            metadata.version += 1
            
            # Save metadata
            ProjectFileManager.write_file_metadata(project_id, metadata)
            
            # Also notify Team conversations to delete their copies
            await ProjectFileManager.notify_team_conversations_file_deleted(
                context=context,
                project_id=project_id,
                filename=filename
            )
            
            return True
            
        except Exception as e:
            logger.exception(f"Error deleting file from project storage: {e}")
            return False

    @staticmethod
    async def notify_team_conversations_file_deleted(
        context: ConversationContext, project_id: str, filename: str
    ) -> None:
        """
        Notifies Team conversations to delete a file that was deleted by the Coordinator.
        
        Args:
            context: Source conversation context
            project_id: Project ID
            filename: Filename to delete
        """
        try:
            # Get Team conversations
            team_conversations = await ProjectFileManager.get_team_conversations(context, project_id)
            if not team_conversations:
                return
            
            # Create clients for Team conversations
            from .project import ConversationClientManager
            
            for conv_id in team_conversations:
                try:
                    client = ConversationClientManager.get_conversation_client(context, conv_id)
                    
                    # Check if file exists in the conversation
                    conversation = await client.get_conversation()
                    files = getattr(conversation, 'files', [])
                    file_exists = any(f.filename == filename for f in files)
                    
                    if file_exists:
                        # Delete the file
                        await client.delete_file(filename)
                        logger.info(f"Deleted file {filename} from Team conversation {conv_id}")
                        
                        # Send notification
                        await client.send_messages(
                            NewConversationMessage(
                                content=f"Coordinator deleted a shared file: {filename}",
                                message_type=MessageType.notice,
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to delete file {filename} from Team conversation {conv_id}: {e}")
        
        except Exception as e:
            logger.exception(f"Error notifying Team conversations about deleted file: {e}")

    @staticmethod
    async def copy_file_to_conversation(
        context: ConversationContext,
        project_id: str,
        filename: str,
        target_conversation_id: str,
    ) -> bool:
        """
        Copies a file from project storage to a target conversation.
        
        Args:
            context: Source conversation context
            project_id: Project ID
            filename: Filename to copy
            target_conversation_id: Target conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First check if the file exists in project storage
            file_path = ProjectFileManager.get_file_path(project_id, filename)
            if not file_path.exists():
                logger.warning(f"File {filename} not found in project storage")
                return False
            
            # Get file metadata
            metadata = ProjectFileManager.read_file_metadata(project_id)
            if not metadata:
                logger.warning(f"No file metadata found for project {project_id}")
                return False
            
            # Find the file metadata
            file_meta = next((f for f in metadata.files if f.filename == filename), None)
            if not file_meta:
                logger.warning(f"No metadata found for file {filename}")
                return False
            
            # Open the file from storage
            with open(file_path, "rb") as f:
                file_content = io.BytesIO(f.read())
            
            # Create client for target conversation
            from .project import ConversationClientManager
            
            target_client = ConversationClientManager.get_conversation_client(context, target_conversation_id)
            if not target_client:
                logger.warning(f"Could not create client for conversation {target_conversation_id}")
                return False
            
            # Check if the file already exists in the target conversation
            conversation = await target_client.get_conversation()
            target_files = getattr(conversation, 'files', [])
            
            file_exists = any(f.filename == filename for f in target_files)
            
            if file_exists:
                # File already exists, update it
                # First delete the existing file
                try:
                    await target_client.delete_file(filename)
                except Exception as e:
                    logger.warning(f"Failed to delete existing file before update: {e}")
                
                # Then upload the new version
                await target_client.write_file(
                    filename=filename,
                    file_content=file_content,
                    content_type=file_meta.content_type
                )
                logger.info(f"Updated file {filename} in conversation {target_conversation_id}")
            else:
                # Upload the file to the target conversation
                await target_client.write_file(
                    filename=filename,
                    file_content=file_content,
                    content_type=file_meta.content_type
                )
                logger.info(f"Copied file {filename} to conversation {target_conversation_id}")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error copying file to conversation: {e}")
            return False

    @staticmethod
    async def get_team_conversations(
        context: ConversationContext, project_id: str
    ) -> List[str]:
        """
        Gets all Team conversation IDs for a project.
        
        Args:
            context: Conversation context
            project_id: Project ID
            
        Returns:
            List of Team conversation IDs
        """
        try:
            # Get linked conversations
            linked_conversations = await ConversationProjectManager.get_linked_conversations(context)
            
            # Filter for team conversations
            team_conversations = []
            for conv_id in linked_conversations:
                # Check if this is a team conversation
                temp_context = await ProjectFileManager.create_temporary_context(context, conv_id)
                if temp_context:
                    role = await ConversationProjectManager.get_conversation_role(temp_context)
                    if role == ProjectRole.TEAM:
                        team_conversations.append(conv_id)
            
            return team_conversations
            
        except Exception as e:
            logger.exception(f"Error getting team conversations: {e}")
            return []

    @staticmethod
    async def create_temporary_context(
        source_context: ConversationContext, target_conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Creates a temporary context for a target conversation.
        
        Args:
            source_context: Source conversation context
            target_conversation_id: Target conversation ID
            
        Returns:
            Temporary ConversationContext or None
        """
        try:
            # Use the helper from ProjectInvitation
            from .project import ProjectInvitation
            
            return await ProjectInvitation.create_temporary_context_for_conversation(
                source_context, target_conversation_id
            )
            
        except Exception as e:
            logger.exception(f"Error creating temporary context: {e}")
            return None

    @staticmethod
    async def synchronize_files_to_team_conversation(
        context: ConversationContext,
        project_id: str,
    ) -> bool:
        """
        Synchronize all project files to a Team conversation.
        
        Args:
            context: Team conversation context
            project_id: Project ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file metadata for the project
            metadata = ProjectFileManager.read_file_metadata(project_id)
            
            if not metadata or not metadata.files:
                return True  # No files to sync
            
            # Identify Coordinator files to sync
            coordinator_files = [f for f in metadata.files if f.is_coordinator_file]
            if not coordinator_files:
                return True  # No Coordinator files to sync
                
            # Create a list for tracking results
            successful_files = []
            failed_files = []
            
            # Copy each file to the Team conversation
            for file_meta in coordinator_files:
                success = await ProjectFileManager.copy_file_to_conversation(
                    context=context,
                    project_id=project_id,
                    filename=file_meta.filename,
                    target_conversation_id=str(context.id),
                )
                
                if success:
                    successful_files.append(file_meta.filename)
                else:
                    failed_files.append(file_meta.filename)
                    logger.warning(f"Failed to copy file {file_meta.filename} to Team conversation")
            
            # Send notification about synchronized files
            if successful_files:
                file_list = ", ".join(successful_files)
                await context.send_messages(
                    NewConversationMessage(
                        content=f"Synchronized shared files from Coordinator: {file_list}",
                        message_type=MessageType.notice,
                    )
                )
            
            # Log the results
            logger.info(f"Synchronized {len(successful_files)} of {len(coordinator_files)} files to Team conversation {context.id}")
            if failed_files:
                logger.warning(f"Failed to synchronize files: {', '.join(failed_files)}")
                
            # Update project log with synchronization event
            if successful_files:
                await ProjectStorage.log_project_event(
                    context=context,
                    project_id=project_id,
                    entry_type="file_synchronization",
                    message=f"Synchronized {len(successful_files)} files to Team conversation",
                    metadata={
                        "successful_files": successful_files,
                        "failed_files": failed_files,
                        "conversation_id": str(context.id)
                    }
                )
            
            return len(failed_files) == 0
            
        except Exception as e:
            logger.exception(f"Error synchronizing files to Team conversation: {e}")
            return False
            
    @staticmethod
    async def get_shared_files(
        context: ConversationContext, project_id: str
    ) -> Dict[str, ProjectFile]:
        """
        Gets all shared files for a project with filename as key.
        
        Args:
            context: Conversation context
            project_id: Project ID
            
        Returns:
            Dictionary of filename to ProjectFile
        """
        try:
            # Get file metadata for the project
            metadata = ProjectFileManager.read_file_metadata(project_id)
            if not metadata or not metadata.files:
                return {}
                
            # Create dictionary with filename as key
            files_dict = {f.filename: f for f in metadata.files}
            return files_dict
            
        except Exception as e:
            logger.exception(f"Error getting shared files: {e}")
            return {}
    
    @staticmethod
    async def process_file_update_notification(
        context: ConversationContext,
        project_id: str,
        update_type: str,
        filename: str
    ) -> bool:
        """
        Processes a file update notification in a Team conversation.
        
        Args:
            context: Conversation context (Team)
            project_id: Project ID
            update_type: Type of update ('file_created', 'file_updated', 'file_deleted')
            filename: Filename that was updated
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First verify that this is a Team conversation
            role = await ConversationProjectManager.get_conversation_role(context)
            if role != ProjectRole.TEAM:
                logger.warning("Only Team conversations should process file update notifications")
                return False
                
            # Process based on update type
            if update_type == "file_created" or update_type == "file_updated":
                # Synchronize the specific file from project storage
                success = await ProjectFileManager.copy_file_to_conversation(
                    context=context,
                    project_id=project_id,
                    filename=filename,
                    target_conversation_id=str(context.id)
                )
                
                action = "added" if update_type == "file_created" else "updated"
                if success:
                    logger.info(f"Successfully {action} file {filename} in Team conversation {context.id}")
                    return True
                else:
                    logger.warning(f"Failed to {action} file {filename} in Team conversation {context.id}")
                    return False
                    
            elif update_type == "file_deleted":
                # Delete the file from this conversation
                try:
                    # Check if file exists
                    conversation = await context.get_conversation()
                    files = getattr(conversation, 'files', [])
                    file_exists = files and any(f.filename == filename for f in files)
                    
                    if file_exists:
                        # Delete the file
                        await context.delete_file(filename)
                        logger.info(f"Deleted file {filename} from Team conversation {context.id}")
                        return True
                    else:
                        # File doesn't exist, nothing to do
                        return True
                        
                except Exception as e:
                    logger.warning(f"Failed to delete file {filename} from Team conversation: {e}")
                    return False
            else:
                logger.warning(f"Unknown file update type: {update_type}")
                return False
                
        except Exception as e:
            logger.exception(f"Error processing file update notification: {e}")
            return False