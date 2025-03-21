# Mission Assistant

A mediator assistant that enables file sharing between conversations in the Semantic Workbench.

## Overview

The Mission Assistant allows users to collaborate across separate conversations by securely sharing files. This enables team members to work together on documents and files without requiring them to be in the same direct conversation.

## Features

- Create invitations to link conversations for file sharing
- Secure invitation validation and acceptance
- Automatic file synchronization between linked conversations
- Conflict detection and resolution for file updates
- Event-based file updates across conversations
- Role-based experience for mission senders and receivers

## Usage

### Commands

#### For Mission Senders
- `/invite [username]` - Invite another user to collaborate
- `/list-participants` - List all users in the mission
- `/revoke [username]` - Revoke a user's access to the mission
- `/mission-status` - View overall mission status

#### For Mission Receivers
- `/join [invitation_code]` - Accept an invitation to collaborate
- `/leave-mission` - Leave the current mission

#### For All Users
- `/list-files` - List shared files in the mission
- `/sync-status [filename]` - Check synchronization status of a file

### Workflow

1. **Creating an Invitation**:
   - In a conversation with the Mission Assistant, use `/invite username`
   - The assistant will create a secure invitation and display an invitation code
   - Share this invitation code with the target user

2. **Accepting an Invitation**:
   - In another conversation with the Mission Assistant, use `/join invitation_code`
   - The assistant will validate the invitation and establish the link
   - Both conversations will be notified of the successful connection

3. **File Sharing**:
   - Upload a file in either linked conversation
   - The file will automatically be synchronized to the other conversation
   - Updates to files will be synchronized in both directions

## Configuration

The Mission Assistant can be configured through the Workbench UI:

- **Auto-sync Files**: Enable/disable automatic file synchronization
- **Invite Command**: Customize the command used for invitations (default: "invite")
- **Join Command**: Customize the command used for accepting invitations (default: "join")
- **Invitation Message**: Customize the message sent to invited users
- **Sender Welcome**: Customize welcome message for mission senders
- **Receiver Welcome**: Customize welcome message for mission receivers
- **Enable Role Features**: Enable/disable role-based command differentiation

## Implementation Details

The assistant uses a secure invitation system that integrates with the Semantic Workbench conversation sharing API. It manages state for linked conversations and tracks file versions to detect conflicts.

For full implementation details, see [IMPLEMENTATION.md](./IMPLEMENTATION.md).

## Testing

To test the Mission Assistant:

1. Create two separate conversations with the Mission Assistant
2. In the first conversation, use `/invite [username]` to invite a user
3. Copy the invitation code from the response
4. In the second conversation, use `/join [invitation_code]` to accept the invitation
5. Upload a file in one conversation and verify it appears in the other
6. Modify a file in one conversation and verify the changes propagate

## Limitations

- File conflict resolution is basic (source wins by default)
- No UI for managing linked conversations or viewing sync status
- Invitation expiration is not enforced by the UI