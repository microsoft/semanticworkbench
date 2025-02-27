# Semantic Workbench Service

## Architecture

The Semantic Workbench service consists of several key components that interact to provide a seamless user experience:

**Workbench Service**: A backend Python service that handles state management, user interactions, conversation history, file storage, and real-time event distribution.

[**Workbench App**](../workbench-app): A single-page web application written in TypeScript and React that provides the user interface for interacting with assistants.

**FastAPI Framework**: Powers the HTTP API and Server-Sent Events (SSE) for real-time updates between clients and assistants.

**Database Layer**: Uses SQLModel (SQLAlchemy) with support for both SQLite (development) and PostgreSQL (production) for persistent storage.

**Authentication**: Integrated Azure AD/Microsoft authentication with JWT token validation.

**Assistants**: Independently developed services that connect to the Workbench through a RESTful API, enabling AI capabilities.

![Architecture Diagram](../docs/images/architecture-animation.gif)

### Core Components

- **Controller Layer**: Implements business logic for conversations, assistants, files, and users
- **Database Models**: SQLModel-based entities for storing application state
- **Authentication**: Azure AD integration with JWT validation
- **File Storage**: Versioned file system for conversation attachments and artifacts
- **Event System**: Real-time event distribution using Server-Sent Events (SSE)
- **API Layer**: RESTful endpoints for all service operations

### Communication

The communication between the Workbench and Assistants is managed through multiple channels:

1. **HTTP API**: RESTful endpoints for CRUD operations and state management
2. **Server-Sent Events (SSE)**: Real-time event streaming for immediate updates
3. **Event System**: Structured event types (e.g., `message.created`, `conversation.updated`) for real-time state synchronization
4. **Webhook Callbacks**: Assistant registration with callback URLs for event delivery

### Database Structure

The service uses SQLModel to manage structured data:

- **Users**: Authentication and profile information
- **Conversations**: Messaging history and metadata
- **Messages**: Different message types with content and metadata
- **Participants**: Users and assistants in conversations
- **Files**: Versioned attachments for conversations
- **Assistants**: Registered assistants and their configurations
- **Shares**: Conversation sharing capabilities

## Features

### Conversation Management
- Create, update, and delete conversations
- Add and remove participants
- Different message types (chat, note, notice, command)
- Message metadata and debug information

### File Management
- File attachment support
- Versioned file storage
- Multiple content types

### Sharing
- Share conversations with other users
- Public/private share links
- Share redemption

### Integration with Assistants
- Assistant registration and discovery
- API key management for secure communication
- Event-based communication

### Speech Services
- Azure Speech integration for text-to-speech

## Configuration

The service is configured through environment variables:

```
# Basic configuration
WORKBENCH_SERVICE_HOST=127.0.0.1
WORKBENCH_SERVICE_PORT=5000

# Database settings
WORKBENCH_SERVICE_DB_CONNECTION=sqlite+aiosqlite:///./workbench-service.db
# Or for PostgreSQL:
# WORKBENCH_SERVICE_DB_CONNECTION=postgresql+asyncpg://user:pass@host:port/dbname

# Authentication
WORKBENCH_SERVICE_TENANT_ID=your-azure-tenant-id
WORKBENCH_SERVICE_CLIENT_ID=your-client-id

# File storage
WORKBENCH_SERVICE_FILES_DIR=./.data/files
```

See the [environment setup guide](../docs/SETUP_DEV_ENVIRONMENT.md) for complete configuration options.

## Setup Guide

### Prerequisites

- Python 3.11+
- Access to database (SQLite for development, PostgreSQL for production)
- Azure AD application registration (for authentication)

### Installing Dependencies

In the [workbench-service](./) directory:

```sh
make
```

This will use [uv](https://github.com/astral-sh/uv) to install all Python dependencies.

If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

### Database Migration

The service uses Alembic for database migrations:

```sh
# Initialize the database
uv run alembic upgrade head
```

### Running from VS Code

To run and/or debug in VS Code:
1. Open the workspace file `semantic-workbench.code-workspace`
2. View->Run
3. Select "service: semantic-workbench-service"

### Running from the Command Line

In the [workbench-service](./) directory:

```sh
uv run start-service [--host HOST] [--port PORT]
```

### Running Tests

```sh
uv run pytest
```

## API Documentation

When running the service, access the FastAPI auto-generated documentation at:

- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## Troubleshooting

### Common Issues

- **Database connection errors**: Verify your connection string and database permissions
- **Authentication failures**: Check your Azure AD configuration and client IDs
- **File storage permissions**: Ensure the service has write access to the files directory

### Debug Mode

Enable debug logging for more detailed information:

```sh
WORKBENCH_SERVICE_LOG_LEVEL=DEBUG uv run start-service
```