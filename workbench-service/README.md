# Semantic Workbench Service

## Architecture

The Semantic Workbench service consists of several key components that interact to provide a seamless user experience:

**Workbench Service**: A backend Python service that handles state management, user interactions, and assists in broker functionalities.

[**Workbench App**](../workbench-app): A single-page web application written in TypeScript and React, compiled into static HTML that runs in the user’s browser.

**FastAPI Framework**: Utilized for the HTTP API, providing endpoints and continuous communication between the Workbench and assistants.

**Assistants**: Independently developed units that connect to the Workbench Service through a RESTful API. Assistants can manage their own state and handle connections to various language models.

![Architecture Diagram](../docs/images/architecture-animation.gif)

### Communication

The communication between the Workbench and Assistants is managed through HTTP requests:

1. **Initialization**: Assistants notify the Workbench about their presence and provide a callback URL.
2. **Message Handling**: Both the Workbench and Assistants can send HTTP requests to each other as needed.
3. **Events**: There are several types of events (e.g., `message created`) that are handled through designated HTTP endpoints.

### Agents

Each assistant (or agent) is registered and maintains its connection through continuous ping requests to the Workbench. This ensures that the state information and response handling remain synchronized.

## Setup Guide

The Semantic Workbench service is a Python service that provides the backend functionality of the Semantic Workbench.

Follow the [setup guide](../docs/SETUP_DEV_ENVIRONMENT.md) to install the development tools.

## Installing dependencies

In the [workbench-service](./) directory

```sh
make
```

If this fails in Windows, try running a vanilla instance of `cmd` or `powershell` and not within `Cmder` or another shell that may have modified the environment.

## Running from VS Code

To run and/or debug in VS Code, View->Run, "service: semantic-workbench-service"

## Running from the command line

In the [workbench-service](./) directory

```sh
uv run start-semantic-workbench
```
