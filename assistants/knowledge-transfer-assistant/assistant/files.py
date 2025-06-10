"""
Project files management module.

This module provides functionality for sharing files between Coordinator and Team conversations.
It enables automatic synchronization of files from Coordinator to Team conversations.
"""

import asyncio
import io
import pathlib
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .common import detect_assistant_role
from .conversation_clients import ConversationClientManager
from .conversation_project_link import ConversationKnowledgePackageManager
from .data import LogEntryType
from .logging import logger
from .storage import ProjectStorage, ProjectStorageManager, read_model, write_model
from .storage_models import ConversationRole


# Define helper function for safe logging without 'filename' conflict
def safe_extra(log_data):
    """Create a safe extra dict for logging without LogRecord conflicts."""
    # Make a copy to avoid modifying the original
    safe_data = log_data.copy()

    # Rename any keys that conflict with LogRecord attributes
    if "filename" in safe_data:
        safe_data["file_name"] = safe_data.pop("filename")
    if "module" in safe_data:
        safe_data["mod_name"] = safe_data.pop("module")
    if "name" in safe_data:
        safe_data["obj_name"] = safe_data.pop("name")

    return safe_data


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


class ProjectFileCollection(BaseModel):
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
        """
        project_dir = ProjectStorageManager.get_project_dir(project_id)
        files_dir = project_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        return files_dir

    @staticmethod
    def get_file_metadata_path(project_id: str) -> pathlib.Path:
        """
        Gets the path to the file metadata JSON.
        """
        files_dir = ProjectFileManager.get_project_files_dir(project_id)
        return files_dir / "file_metadata.json"

    @staticmethod
    def get_file_path(project_id: str, filename: str) -> pathlib.Path:
        """
        Gets the path to a specific file in the project.
        """
        files_dir = ProjectFileManager.get_project_files_dir(project_id)
        return files_dir / filename

    @staticmethod
    def read_file_metadata(project_id: str) -> ProjectFileCollection:
        """
        Reads file metadata for a project.
        """
        path = ProjectFileManager.get_file_metadata_path(project_id)
        return read_model(path, ProjectFileCollection) or ProjectFileCollection(
            files=[],
        )

    @staticmethod
    def write_file_metadata(project_id: str, metadata: ProjectFileCollection) -> pathlib.Path:
        """
        Writes file metadata for a project.
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
        """
        # Create safe log data for debugging
        log_extra = {
            "file_name": file.filename,
            "project_id": project_id,
            "conversation_id": str(context.id),
            "file_size": getattr(file, "file_size", 0),
            "is_coordinator_file": is_coordinator_file,
        }

        try:
            # Verify file information
            if not file.filename:
                logger.error("Missing filename in file metadata", extra=safe_extra(log_extra))
                return False

            # Check if project storage directory exists
            files_dir = ProjectFileManager.get_project_files_dir(project_id)
            if not files_dir.exists():
                logger.debug(f"Creating project files directory: {files_dir}", extra=safe_extra(log_extra))
                files_dir.mkdir(parents=True, exist_ok=True)

            # Read the file from the conversation with error handling
            try:
                buffer = io.BytesIO()
                async with context.read_file(file.filename) as reader:
                    async for chunk in reader:
                        buffer.write(chunk)

                # Verify we got file content
                buffer_size = buffer.tell()
                if buffer_size == 0:
                    logger.error(
                        "Failed to read file content from conversation - buffer is empty", extra=safe_extra(log_extra)
                    )
                    return False

            except Exception as read_error:
                logger.error(f"Error reading file from conversation: {read_error}", extra=safe_extra(log_extra))
                return False

            buffer.seek(0)

            # Write the file to project storage
            file_path = ProjectFileManager.get_file_path(project_id, file.filename)
            try:
                with open(file_path, "wb") as f:
                    f.write(buffer.getvalue())

                # Verify file was written
                if not file_path.exists() or file_path.stat().st_size == 0:
                    logger.error(
                        "Failed to write file to project storage - file is missing or empty",
                        extra=safe_extra(log_extra),
                    )
                    return False

            except Exception as write_error:
                logger.error(f"Error writing file to project storage: {write_error}", extra=safe_extra(log_extra))
                return False

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

            # Add to metadata collection with error handling
            try:
                metadata_path = ProjectFileManager.get_file_metadata_path(project_id)
                logger.debug(f"Reading metadata from {metadata_path}", extra=safe_extra(log_extra))

                metadata = read_model(metadata_path, ProjectFileCollection)
                if not metadata:
                    # Create new collection
                    metadata = ProjectFileCollection(
                        files=[],
                    )

                # Check if file already exists in collection
                existing_idx = next((i for i, f in enumerate(metadata.files) if f.filename == file.filename), None)
                if existing_idx is not None:
                    metadata.files[existing_idx] = file_metadata
                else:
                    metadata.files.append(file_metadata)

                # Save metadata
                ProjectFileManager.write_file_metadata(project_id, metadata)

                # Verify metadata was written
                if not metadata_path.exists():
                    logger.error(f"Failed to write metadata file {metadata_path}", extra=safe_extra(log_extra))
                    return False

                # Final check - verify file appears in metadata
                verification_metadata = read_model(metadata_path, ProjectFileCollection)
                if not verification_metadata:
                    logger.error("Metadata file exists but can't be read", extra=safe_extra(log_extra))
                    return False

                file_exists_in_metadata = any(f.filename == file.filename for f in verification_metadata.files)
                if not file_exists_in_metadata:
                    logger.error(
                        f"File metadata doesn't contain entry for {file.filename}", extra=safe_extra(log_extra)
                    )
                    return False

            except Exception as metadata_error:
                logger.error(f"Error updating metadata: {metadata_error}", extra=safe_extra(log_extra))
                return False

            return True

        except Exception as e:
            logger.exception(f"Error copying file to project storage: {e}", extra=safe_extra(log_extra))
            return False

    @staticmethod
    async def delete_file_from_project_storage(context: ConversationContext, project_id: str, filename: str) -> bool:
        """
        Deletes a file from project storage.
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

            # Save metadata
            ProjectFileManager.write_file_metadata(project_id, metadata)

            # Also notify Team conversations to delete their copies
            await ProjectFileManager.notify_team_conversations_file_deleted(
                context=context, project_id=project_id, filename=filename
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
        """
        try:
            # Get Team conversations
            team_conversations = await ProjectFileManager.get_team_conversations(context, project_id)
            if not team_conversations:
                return

            for conv_id in team_conversations:
                try:
                    client = ConversationClientManager.get_conversation_client(context, conv_id)

                    # Check if file exists in the conversation
                    conversation = await client.get_conversation()
                    files = getattr(conversation, "files", [])
                    file_exists = any(f.filename == filename for f in files)

                    if file_exists:
                        # Delete the file
                        await client.delete_file(filename)
                        logger.debug(f"Deleted file {filename} from Team conversation {conv_id}")

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
        """
        try:
            # Check if the file exists in project storage
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

            # Create client for target conversation
            target_client = ConversationClientManager.get_conversation_client(context, target_conversation_id)
            if not target_client:
                logger.warning(f"Could not create client for conversation {target_conversation_id}")
                return False

            # Read the file content
            try:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()

                if not file_bytes:
                    logger.warning(f"Failed to read file content from {file_path} (empty file)")
                    return False

                file_content = io.BytesIO(file_bytes)
            except Exception as read_error:
                logger.error(f"Failed to read file: {read_error}")
                return False

            # Determine content type
            content_type = file_meta.content_type
            if not content_type:
                content_type = "application/octet-stream"

            # Check if the file exists and delete it first (to handle updates)
            try:
                conversation = await target_client.get_conversation()
                target_files = getattr(conversation, "files", [])
                file_exists = any(f.filename == filename for f in target_files)

                if file_exists:
                    logger.debug(f"File {filename} exists, deleting before upload")
                    await target_client.delete_file(filename)

                    # Brief wait after deletion
                    await asyncio.sleep(1.0)
            except Exception as e:
                logger.error(f"Could not check/delete existing file: {e}")
                # Continue with upload anyway

            # Upload the file
            try:
                file_content.seek(0)  # Reset position to start of file
                await target_client.write_file(filename=filename, file_content=file_content, content_type=content_type)
                logger.debug(f"Successfully uploaded file {filename}")
                return True
            except Exception as upload_error:
                logger.error(f"Failed to upload file: {upload_error}")
                return False

        except Exception as e:
            logger.exception(f"Error copying file to conversation: {e}")
            return False

    @staticmethod
    async def get_team_conversations(context: ConversationContext, project_id: str) -> List[str]:
        """
        Gets all Team conversation IDs for a project.
        """
        try:
            # Get linked conversations
            linked_conversations = await ConversationKnowledgePackageManager.get_linked_conversations(context)

            # Filter for team conversations
            team_conversations = []
            for conv_id in linked_conversations:
                # Check if this is a team conversation
                temp_context = await ProjectFileManager.create_temporary_context(context, conv_id)
                if temp_context:
                    role = await ConversationKnowledgePackageManager.get_conversation_role(temp_context)
                    if role == ConversationRole.TEAM:
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
        """
        try:
            return await ConversationClientManager.create_temporary_context_for_conversation(
                source_context, target_conversation_id
            )

        except Exception as e:
            logger.exception(f"Error creating temporary context: {e}")
            return None

    @staticmethod
    async def synchronize_files_to_team_conversation(
        context: ConversationContext,
        project_id: str,
    ) -> None:
        """
        Synchronize all project files to a Team conversation.
        """
        logger.debug(f"Starting file synchronization for project {project_id}")

        # Get file metadata for the project
        metadata = ProjectFileManager.read_file_metadata(project_id)

        if not metadata or not metadata.files:
            # No metadata found
            await context.send_messages(
                NewConversationMessage(
                    content="No shared files available. The coordinator hasn't shared any files yet.",
                    message_type=MessageType.notice,
                )
            )

        # Identify Coordinator files to sync
        coordinator_files = [f for f in metadata.files if f.is_coordinator_file]

        # Check which files already exist in conversation
        conversation = await context.get_conversation()
        existing_files = getattr(conversation, "files", [])
        existing_filenames = {f.filename for f in existing_files}

        # Track successful and failed files
        successful_files = []
        failed_files = []
        skipped_files = []  # Files that already exist

        # Process each file
        for file_meta in coordinator_files:
            # Skip files that already exist
            if file_meta.filename in existing_filenames:
                skipped_files.append(file_meta.filename)
                continue

            # Try to copy the file
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

        # Create notification message for the user
        available_files = successful_files + skipped_files
        if available_files:
            # Create message about synchronized files
            if successful_files:
                file_list = ", ".join(successful_files)
                message = f"Synchronized files from Coordinator: {file_list}"

                # Add info about skipped files if any
                if skipped_files:
                    existing_list = ", ".join(skipped_files)
                    message += f"\nAlready available: {existing_list}"
            else:
                # Only skipped files
                file_list = ", ".join(skipped_files)
                message = f"All shared files already available: {file_list}"

            # Send notification
            await context.send_messages(
                NewConversationMessage(
                    content=message,
                    message_type=MessageType.notice,
                )
            )

            # Log the synchronization event
            sync_message = (
                f"Synchronized files to Team conversation: {len(successful_files)} new, {len(skipped_files)} existing"
            )

            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.FILE_SHARED,
                message=sync_message,
                metadata={
                    "successful_files": successful_files,
                    "skipped_files": skipped_files,
                    "failed_files": failed_files,
                },
            )

    @staticmethod
    async def get_shared_files(context: ConversationContext, project_id: str) -> Dict[str, ProjectFile]:
        """
        Gets all shared files for a project with filename as key.
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
        context: ConversationContext, project_id: str, update_type: str, filename: str
    ) -> bool:
        """
        Processes a file update notification in a Team conversation.
        """
        try:
            # First verify that this is a Team conversation
            role = await detect_assistant_role(context)

            if role != ConversationRole.TEAM:
                logger.warning("Only Team conversations should process file update notifications")
                return False

            # Process based on update type
            if update_type == "file_created" or update_type == "file_updated":
                # Synchronize the specific file from project storage
                success = await ProjectFileManager.copy_file_to_conversation(
                    context=context, project_id=project_id, filename=filename, target_conversation_id=str(context.id)
                )

                action = "added" if update_type == "file_created" else "updated"
                if success:
                    return True
                else:
                    logger.warning(f"Failed to {action} file {filename} in Team conversation {context.id}")
                    return False

            elif update_type == "file_deleted":
                # Delete the file from this conversation
                try:
                    # Check if file exists
                    conversation = await context.get_conversation()
                    files = getattr(conversation, "files", [])
                    file_exists = files and any(f.filename == filename for f in files)

                    if file_exists:
                        # Delete the file
                        await context.delete_file(filename)
                        logger.debug(f"Deleted file {filename} from Team conversation {context.id}")
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
