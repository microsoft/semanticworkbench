# Understanding how the Knowledge Transfer Assistant

The Knowledge Transfer Assistant isn't simply a chat conversation with an assistant.

It uses a "more code than model", recipe-inspired approach that runs "meta-cognitive operations" to create an assistant that guides users through the knowledge transfer process.

The Knowledge Transfer Assistant is an assistant experience that runs within _MADE: Exploration's_ Semantic Workbench.

## How it works

The Knowledge Transfer Assistant uses a multi-conversation architecture to separate knowledge creation from knowledge consumption, addressing the confusion that arises when multiple participants work in the same shared conversation.

### Dual-Conversation Architecture

The system operates through two conversation types:

1. **Coordinator Conversation**: Where knowledge creators collaborate to structure and package their knowledge
2. **Team Conversations**: Individual conversations created for each team member who joins the knowledge transfer

### Knowledge Artifacts

The system structures informal knowledge into four transferable artifacts:

- **Knowledge Brief**: Context, scope, and timeline summary
- **Knowledge Digest**: An organized outline of all knowledge from coordinator conversations and attachments, automatically updated by LLM analysis. Contains high information density with key concepts, decisions, facts, and context—serving as the primary knowledge reference for team members
- **Learning Objectives**: Structured goals with measurable outcomes
- **Information Requests**: Bidirectional Q&A channel with priority levels

### Cross-Conversation Communication

Isolated conversations communicate through centralized components:

- **Share Storage**: Maintains knowledge packages and progress across conversations
- **Share Manager**: Creates shareable team conversations via secure URLs
- **Notifications System**: Enables updates between coordinators and team members
- **File Synchronization**: Propagates documents across relevant conversations

### User Experience

**Coordinators:**
- Navigate to https://semantic-workbench.azurewebsites.net/ and start a new conversation with the Knowledge Transfer Assistant.
- The assistant will guide you through:
    - Define learning objectives
    - Develop content through natural conversation and file attachments
    - Create a knowledge brief and invitation messages for your team members
    - Share the provided Share Link with your team members.
- Monitor team progress via real-time dashboards and notifications
- Respond to information requests

**Team Members:**
- Join a new conversation via the coordinator-provided share URL, creating individual conversation
- Receive personalized welcome and knowledge brief
- Work through objectives with assistant guidance
- Access synchronized files and updated digest
- Submit questions through information requests

### Technical Implementation

The system uses orchestration logic to coordinate multiple AI assistants rather than relying on a single large model. This enables role-specific assistant behavior, persistent state across conversation boundaries, and real-time synchronization between coordinator and team conversations.

The architecture allows multiple team members to join knowledge transfers independently while maintaining separation between knowledge creation and consumption workflows.
