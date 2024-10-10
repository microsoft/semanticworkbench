# Semantic Workbench App

## Architecture

The Semantic Workbench app is designed as a client-side, single-page application (SPA) using React and TypeScript. It runs entirely in the user's browser and interacts with the backend Semantic Workbench service for state and conversation management.

### Key Components

**React/TypeScript**: The app is built using the React library and TypeScript for static typing.

**Client-Server Interaction**: The app communicates with the Workbench backend service via RESTful APIs, performing AJAX requests to handle user input and display responses.

**Single Page Application (SPA)**: Ensures smooth and seamless transitions between different parts of the app without requiring full page reloads.

### Initialization and Authentication

The application requires user authentication, typically via Microsoft AAD or MSA accounts. Instructions for setting up the development environment are in the repo readme. To deploy in your own environment see [app registration documentation](../docs/CUSTOM_APP_REGISTRATION.md).

### Connecting to the Backend Service

The Semantic Workbench app connects to the backend service using RESTful API calls. Here’s how the interaction works:

1. **Initial Setup**: On application startup, the app establishes a connection to the backend service located at a specified endpoint. This connection requires SSL certificates, which may prompt for admin credentials when installed during local development.
2. **User Authentication**: Users must authenticate via Microsoft AAD or MSA accounts. This enables secure access and interaction between the app and the backend.
3. **Data Fetching**: The app makes AJAX requests to the backend service, fetching data such as message history, user sessions, and conversation context.
4. **Event Handling**: User actions within the app (e.g., sending a message) trigger RESTful API calls to the backend, which processes the actions and returns the appropriate responses.
5. **State Management**: The backend service keeps track of the conversation state and other relevant information, enabling the app to provide a consistent user experience.

#### Error Handling

The app includes error handling mechanisms that notify users of any issues with the backend connection, such as authentication failures or network issues.


## Setup Guide

The Semantic Workbench app is a React/Typescript app integrated with the [Semantic Workbench](../workbench-service/README.md) backend service.

Follow the [setup guide](../docs/SETUP_DEV_ENVIRONMENT.md) to install the development tools.

## Installing dependencies

In the [workbench-app](./) directory

```sh
make
```

## Running from VS Code

To run and/or debug in VS Code, View->Run, "app: semantic-workbench-app"

## Running from the command line

In the [workbench-app](./) directory

```sh
pnpm start
```

Note: you might be prompted for admin credentials for the SSL certificates used by the app.

## Extra information

### Scripts

-   `pnpm start` - start dev server
-   `pnpm build` - build for production
-   `pnpm preview` - locally preview production build

### More info

-   [Message Metadata](./docs/MESSAGE_METADATA.md)
-   [Message Types](./docs/MESSAGE_TYPES.md)
-   [State Inspectors](./docs/STATE_INSPECTORS.md)
