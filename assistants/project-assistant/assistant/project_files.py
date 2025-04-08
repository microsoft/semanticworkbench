"""
Project files management module.

This module provides functionality for sharing files between Coordinator and Team conversations.
It enables automatic synchronization of files from Coordinator to Team conversations.
"""

import io
import pathlib
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage
from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import extra_data, logger
from .project_data import BaseEntity, LogEntryType
from .project_storage import (
    ConversationProjectManager,
    ProjectRole,
    ProjectStorage,
    ProjectStorageManager,
    read_model,
    write_model,
)


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


# logger is now imported from .logging


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
    async def delete_file_from_project_storage(context: ConversationContext, project_id: str, filename: str) -> bool:
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
            from .conversation_clients import ConversationClientManager

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
        # IMPORTANT: Don't use 'filename' as a key in log_extra since it conflicts with LogRecord's internal attribute
        log_extra = {
            "conversation_id": str(context.id),
            "target_conversation_id": target_conversation_id,
            "project_id": project_id,
            "file_name": filename,  # Changed from 'filename' to 'file_name' to avoid conflict
        }

        try:
            logger.info(
                f"Starting file copy: {filename} to conversation {target_conversation_id}", extra=safe_extra(log_extra)
            )

            # First check if the file exists in project storage
            file_path = ProjectFileManager.get_file_path(project_id, filename)
            if not file_path.exists():
                logger.warning(
                    f"File {filename} not found in project storage: {file_path}", extra=safe_extra(log_extra)
                )
                return False

            # Get file size
            file_size = file_path.stat().st_size
            logger.info(f"Found file in storage: {filename}, size: {file_size} bytes", extra=safe_extra(log_extra))

            # Get file metadata
            metadata = ProjectFileManager.read_file_metadata(project_id)
            if not metadata:
                logger.warning(f"No file metadata found for project {project_id}", extra=safe_extra(log_extra))
                return False

            # Find the file metadata
            file_meta = next((f for f in metadata.files if f.filename == filename), None)
            if not file_meta:
                logger.warning(f"No metadata found for file {filename}", extra=safe_extra(log_extra))
                return False

            # Add additional metadata but don't include the file_meta directly as it might have a filename attribute
            metadata_extra = extra_data(file_meta)
            # Avoid any key conflicts with LogRecord
            if "filename" in metadata_extra:
                metadata_extra["file_meta_name"] = metadata_extra.pop("filename")

            logger.info(
                f"Found file metadata: {file_meta.filename}, type: {file_meta.content_type}, size: {file_meta.file_size}",
                extra=dict(**log_extra, **metadata_extra),
            )

            # Open the file from storage
            logger.debug(f"Reading file content from {file_path}", extra=safe_extra(log_extra))
            with open(file_path, "rb") as f:
                file_content = io.BytesIO(f.read())
                read_size = file_content.getbuffer().nbytes
                logger.debug(f"Read {read_size} bytes from file {filename}", extra=safe_extra(log_extra))

            # Create client for target conversation
            from .conversation_clients import ConversationClientManager

            logger.debug(
                f"Creating client for target conversation {target_conversation_id}", extra=safe_extra(log_extra)
            )
            target_client = ConversationClientManager.get_conversation_client(context, target_conversation_id)
            if not target_client:
                logger.warning(
                    f"Could not create client for conversation {target_conversation_id}", extra=safe_extra(log_extra)
                )
                return False

            # Check if the file already exists in the target conversation
            logger.debug(
                f"Checking if file exists in conversation {target_conversation_id}", extra=safe_extra(log_extra)
            )

            # Check for file existence
            file_exists = False
            target_files = []

            # Try file_exists method first if available (most direct)
            try:
                if hasattr(target_client, "file_exists") and callable(getattr(target_client, "file_exists")):
                    file_exists_method = getattr(target_client, "file_exists")
                    file_exists = await file_exists_method(filename)
                    logger.debug(f"Used file_exists() API check - result: {file_exists}", extra=safe_extra(log_extra))

                    # If file doesn't exist, still get the file list for logging
                    if not file_exists:
                        conversation = await target_client.get_conversation()
                        target_files = getattr(conversation, "files", [])
                else:
                    # Fallback to get_conversation
                    logger.debug("file_exists() not available, using get_conversation()", extra=safe_extra(log_extra))
                    conversation = await target_client.get_conversation()
                    target_files = getattr(conversation, "files", [])
                    file_exists = any(f.filename == filename for f in target_files)
            except Exception as e:
                logger.warning(f"Error checking existing files: {e}", extra=safe_extra(log_extra))
                # Continue with empty list if we can't check

            logger.debug(f"Found {len(target_files)} files in target conversation", extra=safe_extra(log_extra))

            if file_exists:
                logger.info(
                    f"File {filename} already exists in conversation {target_conversation_id}, updating",
                    extra=safe_extra(log_extra),
                )
                # File already exists, update it
                # First delete the existing file with retry
                delete_success = False
                for delete_attempt in range(3):  # Try deletion up to 3 times
                    try:
                        logger.debug(
                            f"Deleting existing file {filename} before update (attempt {delete_attempt + 1}/3)",
                            extra=safe_extra(log_extra),
                        )
                        await target_client.delete_file(filename)
                        delete_success = True
                        logger.info(
                            f"Successfully deleted existing file (attempt {delete_attempt + 1})",
                            extra=safe_extra(log_extra),
                        )
                        break
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete existing file (attempt {delete_attempt + 1}): {e}",
                            extra=safe_extra(log_extra),
                        )
                        # Short delay before retry
                        import asyncio

                        await asyncio.sleep(1.0)

                if not delete_success:
                    logger.warning(
                        f"Could not delete existing file {filename} after all attempts. Will try to upload anyway.",
                        extra=safe_extra(log_extra),
                    )
                    # Continue despite delete failure - the upload might overwrite

                # Then upload the new version with retry
                logger.debug(f"Uploading new version of file {filename}", extra=safe_extra(log_extra))

                upload_success = False
                upload_error = None
                for upload_attempt in range(3):  # Try upload up to 3 times
                    try:
                        logger.debug(f"Update upload attempt {upload_attempt + 1}/3", extra=safe_extra(log_extra))
                        file_content.seek(0)  # Reset position for each attempt
                        await target_client.write_file(
                            filename=filename, file_content=file_content, content_type=file_meta.content_type
                        )
                        upload_success = True
                        logger.info(
                            f"Update upload attempt {upload_attempt + 1} succeeded", extra=safe_extra(log_extra)
                        )
                        break
                    except Exception as e:
                        upload_error = e
                        logger.warning(
                            f"Update upload attempt {upload_attempt + 1} failed: {e}", extra=safe_extra(log_extra)
                        )
                        # Short delay before retry
                        import asyncio

                        await asyncio.sleep(1.0)

                if not upload_success:
                    logger.error(
                        f"All update upload attempts failed for file {filename}: {upload_error}",
                        extra=safe_extra(log_extra),
                    )
                    return False

                # Use a similar approach to the file upload verification
                # Don't use retry logic but just a single longer delay
                try:
                    import asyncio

                    # Use a longer delay (10 seconds) to allow the API time to process the update
                    logger.info(
                        f"Waiting 10s to allow API to process file update for {filename}",
                        extra=safe_extra(log_extra),
                    )
                    await asyncio.sleep(10.0)

                    # Check if the file is visible after the delay (for debugging only)
                    try:
                        # Get conversation object directly - more reliable than list_files
                        logger.info("Using get_conversation() to check files after update", extra=safe_extra(log_extra))
                        updated_conversation = await target_client.get_conversation()
                        updated_files = getattr(updated_conversation, "files", [])

                        # Try direct file_exists check
                        if hasattr(target_client, "file_exists") and callable(getattr(target_client, "file_exists")):
                            try:
                                file_exists_method = getattr(target_client, "file_exists")
                                file_exists = await file_exists_method(filename)
                                logger.info(
                                    f"Used file_exists() API check after update - result: {file_exists}",
                                    extra=safe_extra(log_extra),
                                )
                            except Exception as ex:
                                logger.debug(
                                    f"file_exists check failed after update: {ex}", extra=safe_extra(log_extra)
                                )
                                # Continue with standard verification
                    except Exception as e:
                        logger.warning(f"Error checking files with API after update: {e}", extra=safe_extra(log_extra))
                        updated_files = []

                    # Log what we found
                    file_count = len(updated_files) if updated_files else 0
                    file_names = [f.filename for f in updated_files] if updated_files else []
                    logger.info(
                        f"After 10s delay, found {file_count} files in conversation: {file_names}",
                        extra=safe_extra(log_extra),
                    )

                    # Check for our file
                    file_verified = any(f.filename == filename for f in updated_files)
                    if file_verified:
                        logger.info(f"File {filename} is now visible after update", extra=safe_extra(log_extra))
                    else:
                        logger.info(
                            f"File {filename} not yet visible after update - this is expected with API caching",
                            extra=safe_extra(log_extra),
                        )
                except Exception as e:
                    logger.warning(f"Error checking file update: {e}", extra=safe_extra(log_extra))
                    # Continue anyway assuming the update worked

                logger.info(
                    f"Successfully updated file {filename} in conversation {target_conversation_id}",
                    extra=safe_extra(log_extra),
                )
            else:
                # Upload the file to the target conversation
                logger.debug(
                    f"Uploading new file {filename} to conversation {target_conversation_id}",
                    extra=safe_extra(log_extra),
                )
                file_content.seek(0)  # Make sure to reset to beginning of file

                # Add retry logic for the file upload operation
                upload_success = False
                upload_error = None
                for upload_attempt in range(3):  # Try up to 3 times
                    try:
                        logger.debug(f"File upload attempt {upload_attempt + 1}/3", extra=safe_extra(log_extra))
                        file_content.seek(0)  # Reset position for each attempt
                        await target_client.write_file(
                            filename=filename, file_content=file_content, content_type=file_meta.content_type
                        )
                        upload_success = True
                        logger.info(f"Upload attempt {upload_attempt + 1} succeeded", extra=safe_extra(log_extra))
                        break
                    except Exception as e:
                        upload_error = e
                        logger.warning(f"Upload attempt {upload_attempt + 1} failed: {e}", extra=safe_extra(log_extra))
                        # Short delay before retry
                        import asyncio

                        await asyncio.sleep(1.0)

                if not upload_success:
                    logger.error(
                        f"All upload attempts failed for file {filename}: {upload_error}", extra=safe_extra(log_extra)
                    )
                    return False

                logger.info(
                    f"Successfully copied file {filename} to conversation {target_conversation_id}",
                    extra=safe_extra(log_extra),
                )

            # File uploads appear to work with the API but verification consistently fails
            # due to known eventual consistency issues in the Workbench API

            # Instead of attempting multiple verifications, we'll use a simpler approach
            try:
                import asyncio

                # Use a longer delay (10 seconds) to give the API more time for background processing
                logger.info(
                    f"Waiting 10s to allow API to process file upload for {filename}",
                    extra=safe_extra(log_extra),
                )
                await asyncio.sleep(10.0)

                # Check if the file is visible after the delay
                try:
                    # Get conversation object and extract files - more reliable than list_files
                    logger.info("Using get_conversation() to check files", extra=safe_extra(log_extra))
                    new_conversation = await target_client.get_conversation()
                    new_target_files = getattr(new_conversation, "files", [])

                    # Try direct file_exists check first
                    file_verified = False
                    if hasattr(target_client, "file_exists") and callable(getattr(target_client, "file_exists")):
                        try:
                            file_exists_method = getattr(target_client, "file_exists")
                            file_exists = await file_exists_method(filename)
                            logger.info(
                                f"Used file_exists() API check - result: {file_exists}", extra=safe_extra(log_extra)
                            )
                            if file_exists:
                                file_verified = True
                        except Exception as ex:
                            logger.debug(f"file_exists check failed: {ex}", extra=safe_extra(log_extra))
                            # Continue to standard verification
                except Exception as e:
                    logger.warning(f"Error checking files with API: {e}", extra=safe_extra(log_extra))
                    new_target_files = []

                # Get more detailed information for debugging
                file_count = len(new_target_files) if new_target_files else 0
                file_names = [f.filename for f in new_target_files] if new_target_files else []
                logger.info(
                    f"After 10s delay, found {file_count} files in conversation: {file_names}",
                    extra=safe_extra(log_extra),
                )

                # Check if the file is there, but only for logging purposes
                file_verified = any(f.filename == filename for f in new_target_files)
                if file_verified:
                    logger.info(f"File {filename} is now visible in conversation", extra=safe_extra(log_extra))
                else:
                    logger.info(
                        f"File {filename} not yet visible in API response - this is expected with API caching",
                        extra=safe_extra(log_extra),
                    )

                # IMPORTANT: We always return success since the upload API call worked
                # The file will eventually appear in the conversation, but the API has
                # eventual consistency issues that prevent immediate verification
                logger.info(
                    f"File upload operation for {filename} considered successful based on upload API response",
                    extra=safe_extra(log_extra),
                )
                return True
            except Exception as e:
                logger.warning(
                    f"Error in verification, but upload succeeded so continuing: {e}", extra=safe_extra(log_extra)
                )
                # Even if verification process has errors, consider it a success
                # as long as the upload API call worked
                return True

            return True

        except Exception as e:
            logger.exception(f"Error copying file to conversation: {e}", extra=safe_extra(log_extra))
            return False

    @staticmethod
    async def get_team_conversations(context: ConversationContext, project_id: str) -> List[str]:
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
            # Use the helper from ConversationClientManager
            from .conversation_clients import ConversationClientManager

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
    ) -> bool:
        """
        Synchronize all project files to a Team conversation.

        Args:
            context: Team conversation context
            project_id: Project ID

        Returns:
            True if successful, False otherwise
        """
        # Create safe logging data without filename field to avoid conflicts
        log_data = {
            "conversation_id": str(context.id),
            "project_id": project_id,
            "function": "synchronize_files_to_team_conversation",
        }

        try:
            # Get file metadata for the project
            logger.info(f"Starting file synchronization for project {project_id}", extra=safe_extra(log_data))

            metadata = ProjectFileManager.read_file_metadata(project_id)

            if not metadata or not metadata.files:
                logger.info("No files found in project metadata", extra=safe_extra(log_data))
                return True  # No files to sync

            # Log files found
            file_names = [f.filename for f in metadata.files]
            logger.info(
                f"Found {len(metadata.files)} files in project metadata: {file_names}", extra=safe_extra(log_data)
            )

            # Identify Coordinator files to sync
            coordinator_files = [f for f in metadata.files if f.is_coordinator_file]
            if not coordinator_files:
                logger.info("No Coordinator files to sync", extra=safe_extra(log_data))
                return True  # No Coordinator files to sync

            # Create a list for tracking results
            successful_files = []
            failed_files = []

            # Copy each file to the Team conversation with multiple attempts
            import asyncio

            max_sync_attempts = 3  # Try each file up to 3 times

            for file_meta in coordinator_files:
                # Safe log data for this specific file (without using 'filename' key)
                file_log_data = {**log_data, "file_name": file_meta.filename}

                logger.info(f"Copying file {file_meta.filename} to Team conversation", extra=safe_extra(file_log_data))

                # Try multiple times for each file
                file_sync_success = False
                for sync_attempt in range(max_sync_attempts):
                    logger.info(
                        f"File sync attempt {sync_attempt + 1}/{max_sync_attempts} for {file_meta.filename}",
                        extra=safe_extra(file_log_data),
                    )

                    # Check for the file before uploading (to avoid duplicates)
                    try:
                        # Use list_files() method for more reliable file detection
                        target_files = []
                        # Don't try to use list_files - it returns data in a different format than expected
                        # Just use the more reliable get_conversation method
                        logger.debug(
                            "Using get_conversation() to check for existing file", extra=safe_extra(file_log_data)
                        )
                        conversation = await context.get_conversation()
                        target_files = getattr(conversation, "files", [])

                        # Try direct file_exists check if available
                        file_exists = False
                        if hasattr(context, "file_exists") and callable(getattr(context, "file_exists")):
                            try:
                                file_exists_method = getattr(context, "file_exists")
                                file_exists = await file_exists_method(file_meta.filename)
                                logger.debug(
                                    f"Used file_exists() API - result: {file_exists}", extra=safe_extra(file_log_data)
                                )
                            except Exception as ex:
                                logger.debug(f"file_exists check failed: {ex}", extra=safe_extra(file_log_data))
                                # Continue to fallback check

                        # Fallback to list check if file_exists not available or failed
                        if not file_exists:
                            file_exists = any(f.filename == file_meta.filename for f in target_files)

                        if file_exists:
                            logger.info(
                                f"File {file_meta.filename} already exists in conversation {context.id}",
                                extra=safe_extra(file_log_data),
                            )
                            # Consider this a success without re-uploading
                            file_sync_success = True
                            break
                    except Exception as e:
                        logger.warning(f"Error checking for existing file: {e}", extra=safe_extra(file_log_data))
                        # Continue to upload attempt

                    # Attempt the file copy
                    success = await ProjectFileManager.copy_file_to_conversation(
                        context=context,
                        project_id=project_id,
                        filename=file_meta.filename,
                        target_conversation_id=str(context.id),
                    )

                    if success:
                        file_sync_success = True
                        logger.info(
                            f"Successfully copied file {file_meta.filename} (attempt {sync_attempt + 1})",
                            extra=safe_extra(file_log_data),
                        )
                        break
                    else:
                        logger.warning(
                            f"Failed to copy file {file_meta.filename} (attempt {sync_attempt + 1})",
                            extra=safe_extra(file_log_data),
                        )
                        # Add delay before retry
                        await asyncio.sleep(1.0 + sync_attempt)  # Progressive backoff

                # Record final result for this file
                if file_sync_success:
                    successful_files.append(file_meta.filename)
                    logger.info(
                        f"Successfully copied file {file_meta.filename} to Team conversation",
                        extra=safe_extra(file_log_data),
                    )
                else:
                    failed_files.append(file_meta.filename)
                    logger.warning(
                        f"Failed to copy file {file_meta.filename} to Team conversation after all attempts",
                        extra=safe_extra(file_log_data),
                    )

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
            logger.info(
                f"Synchronized {len(successful_files)} of {len(coordinator_files)} files to Team conversation {context.id}",
                extra=safe_extra(log_data),
            )
            if failed_files:
                # Log failures with safe extra data
                failure_log_data = {
                    **log_data,
                    "failed_count": len(failed_files),
                    "failed_files_list": ", ".join(failed_files),
                }
                logger.warning(
                    f"Failed to synchronize files: {', '.join(failed_files)}", extra=safe_extra(failure_log_data)
                )

            # Update project log with synchronization event
            if successful_files:
                # Create safe metadata for project log (avoid using "filename" key)
                log_metadata = {
                    "successful_file_names": successful_files,
                    "failed_file_names": failed_files,
                    "conversation_id": str(context.id),
                    "successful_count": len(successful_files),
                    "failed_count": len(failed_files),
                }

                await ProjectStorage.log_project_event(
                    context=context,
                    project_id=project_id,
                    entry_type=LogEntryType.FILE_SHARED,
                    message=f"Synchronized {len(successful_files)} files to Team conversation",
                    metadata=log_metadata,
                )

            return len(failed_files) == 0

        except Exception as e:
            # Log exception with safe data
            logger.exception(f"Error synchronizing files to Team conversation: {e}", extra=safe_extra(log_data))
            return False

    @staticmethod
    async def get_shared_files(context: ConversationContext, project_id: str) -> Dict[str, ProjectFile]:
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
        context: ConversationContext, project_id: str, update_type: str, filename: str
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
                    context=context, project_id=project_id, filename=filename, target_conversation_id=str(context.id)
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
                    files = getattr(conversation, "files", [])
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
