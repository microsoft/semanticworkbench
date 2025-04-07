## 🔄 IN PROGRESS: File Sharing Implementation

The goal is to implement a file sharing system between Coordinator and Team conversations where:

1. **Requirements**:
   - When a Coordinator adds, updates, or deletes files in their conversation, copies are maintained in the project data directory
   - When Team members join a project, all files from the project data directory are copied to their conversation
   - When Team members receive notifications of file changes, their local copies are updated
   - Files added by Team members work normally but aren't shared with the project

2. **Research Findings**:
   - Files in Semantic Workbench are associated with specific conversations
   - The `ConversationContext` provides methods for file operations:
     - `context.list_files()`: List files in a conversation
     - `context.write_file()`: Upload a file to a conversation
     - `context.read_file()`: Download a file from a conversation
     - `context.delete_file()`: Delete a file from a conversation
     - `context.file_exists()`: Check if a file exists
     - `context.get_file()`: Get file metadata
   - File events are captured through event handlers:
     - `@assistant.events.conversation.file.on_created`
     - `@assistant.events.conversation.file.on_updated`
     - `@assistant.events.conversation.file.on_deleted` (not yet implemented in project-assistant)
   - Cross-conversation notifications are handled by the `ProjectNotifier` class:
     - `ProjectNotifier.send_notice_to_linked_conversations()`: Sends notices to related conversations
     - `ProjectNotifier.notify_project_update()`: Sends notices and refreshes UI panels
   - Files have metadata including filename, conversation_id, content_type, file_size, participant information

3. **Implementation Plan**:

   a. **File Models & Storage Structure**:
      - Create a `ProjectFile` model to track files in a project
      - Create a shared directory structure for project files
      - Implement methods to read/write files to the shared directory

   b. **File Event Handlers**:
      - Enhance `on_file_created` handler in chat.py to copy Coordinator files to project storage
      - Implement `on_file_deleted` handler to remove files from project storage
      - Enhance existing handlers to notify Team conversations about file changes

   c. **File Synchronization Logic**:
      - Create a `ProjectFileManager` class with methods to:
        - Copy files between conversations
        - Synchronize files from project storage to a new Team conversation
        - Check and update files when Team conversations get notifications
      - Add methods to check file ownership and determine sharing behavior

   d. **Project Join Enhancement**:
      - Modify `ProjectInvitation.redeem_invitation` to synchronize files when a Team member joins
      - Ensure all project files are copied to the Team conversation during join

   e. **UI and User Experience**:
      - Enhance notifications about file sharing
      - Add visual indicators for shared vs. local files
      - Implement commands for managing file sharing

4. **Detailed Implementation Steps**:

   a. **Create a ProjectFile Model and Storage Manager**:
   ```python
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
       is_coordinator_file: bool  # Whether this file was created by Coordinator

   class ProjectFileManager:
       """Manages shared project files."""

       @staticmethod
       def get_project_files_dir(project_id: str) -> pathlib.Path:
           """Gets the directory for project files."""
           shared_dir = ProjectStorageManager.get_shared_dir(project_id)
           files_dir = shared_dir / "files"
           files_dir.mkdir(parents=True, exist_ok=True)
           return files_dir

       @staticmethod
       def get_file_metadata_path(project_id: str) -> pathlib.Path:
           """Gets the path to the file metadata JSON."""
           files_dir = ProjectFileManager.get_project_files_dir(project_id)
           return files_dir / "file_metadata.json"

       @staticmethod
       def get_file_path(project_id: str, filename: str) -> pathlib.Path:
           """Gets the path to a specific file in the project."""
           files_dir = ProjectFileManager.get_project_files_dir(project_id)
           return files_dir / filename
   ```

   b. **Implement File Copy Functions**:
   ```python
   @staticmethod
   async def copy_file_to_project_storage(
       context: ConversationContext,
       project_id: str,
       file: workbench_model.File,
       is_coordinator_file: bool = True
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
           with open(file_path, 'wb') as f:
               f.write(buffer.getvalue())

           # Store file metadata
           file_metadata = ProjectFile(
               file_id=str(file.id),
               filename=file.filename,
               content_type=file.content_type,
               file_size=file.file_size,
               created_by=file.participant_id,
               created_at=file.created_datetime,
               updated_at=file.updated_datetime,
               updated_by=file.participant_id,
               is_coordinator_file=is_coordinator_file
           )

           # Add to metadata collection
           metadata_path = ProjectFileManager.get_file_metadata_path(project_id)
           metadata = read_model(metadata_path, ProjectFileCollection) or ProjectFileCollection(files=[])

           # Check if file already exists in collection
           existing_idx = next((i for i, f in enumerate(metadata.files) if f.filename == file.filename), None)
           if existing_idx is not None:
               metadata.files[existing_idx] = file_metadata
           else:
               metadata.files.append(file_metadata)

           # Save metadata
           write_model(metadata_path, metadata)

           return True

       except Exception as e:
           logger.exception(f"Error copying file to project storage: {e}")
           return False
   ```

   c. **Enhance File Event Handlers**:
   ```python
   @assistant.events.conversation.file.on_created
   async def on_file_created(
       context: ConversationContext,
       event: workbench_model.ConversationEvent,
       file: workbench_model.File,
   ) -> None:
       """
       Handle when a file is created in the conversation.
       If the file is created by a Coordinator, it's copied to project storage
       and synchronized to all Team conversations.
       """
       try:
           # Get project ID and role
           project_id = await ProjectManager.get_project_id(context)
           if not project_id or not file.filename:
               return

           role = await ConversationProjectManager.get_conversation_role(context)
           if not role:
               return

           # Log file creation to project log
           await ProjectStorage.log_project_event(
               context=context,
               project_id=project_id,
               entry_type="file_shared",
               message=f"File shared: {file.filename}",
           )

           # If Coordinator file, copy to project storage and notify Team
           if role == ProjectRole.COORDINATOR:
               # Copy file to project storage
               success = await ProjectFileManager.copy_file_to_project_storage(
                   context=context,
                   project_id=project_id,
                   file=file,
                   is_coordinator_file=True
               )

               if success:
                   # Get all team conversations
                   team_conversations = await ConversationProjectManager.get_team_conversations(context, project_id)

                   # Copy file to all team conversations
                   for conv_id in team_conversations:
                       await ProjectFileManager.copy_file_to_conversation(
                           context=context,
                           project_id=project_id,
                           filename=file.filename,
                           target_conversation_id=conv_id
                       )

                   # Notify team about new file
                   await ProjectNotifier.notify_project_update(
                       context=context,
                       project_id=project_id,
                       update_type="file_created",
                       message=f"Coordinator shared a new file: {file.filename}"
                   )

       except Exception as e:
           logger.exception(f"Error handling file creation: {e}")
   ```

   d. **Add File Synchronization to Team Join Process**:
   ```python
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
           metadata_path = ProjectFileManager.get_file_metadata_path(project_id)
           metadata = read_model(metadata_path, ProjectFileCollection)

           if not metadata or not metadata.files:
               return True  # No files to sync

           # Copy each file to the Team conversation
           for file_meta in metadata.files:
               if file_meta.is_coordinator_file:  # Only sync Coordinator files
                   success = await ProjectFileManager.copy_file_to_conversation(
                       context=context,
                       project_id=project_id,
                       filename=file_meta.filename,
                       target_conversation_id=str(context.id)
                   )

                   if not success:
                       logger.warning(f"Failed to copy file {file_meta.filename} to Team conversation")

           return True

       except Exception as e:
           logger.exception(f"Error synchronizing files to Team conversation: {e}")
           return False
   ```

   e. **Modify Project Join Logic**:
   ```python
   # In ProjectInvitation.redeem_invitation
   # After successful join:
   # Synchronize files from project storage to Team conversation
   await ProjectFileManager.synchronize_files_to_team_conversation(
       context=context,
       project_id=project_id
   )
   ```

5. **Testing Strategy**:
   - Test file creation by Coordinator and verify it appears in Team conversations
   - Test file updates and verify changes propagate correctly
   - Test file deletion and verify it's removed from all Team conversations
   - Test file creation by Team member and verify it remains local
   - Test joining a project with existing files and verify all files are copied
   - Test edge cases: large files, special characters in filenames, etc.

This implementation will create a seamless file sharing experience between Coordinator and Team conversations while maintaining proper separation between shared project files and local Team files.