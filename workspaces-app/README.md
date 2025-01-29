# High-Level Plan for AI Assistant Chat Application

This project creates an AI assistant chat experience using a React and TypeScript frontend built with Vite and RTK Query, interacting with a backend Python REST service. We are using Fluent UI React v9 for the UI components to enhance the app's appearance and user experience.

**Development Plan:**

1. **Initialize Project**
   - Create a new Vite project with React and TypeScript.
   - Set up project structure for components and services.

2. **Set Up State Management and Styling**
   - Integrate Redux Toolkit and RTK Query for efficient state management and data fetching.

3. **Develop Chat Interface with Fluent UI React**
   - Use Fluent UI React components to create user interface elements for the chat experience.
   - Implement styling and responsiveness using Fluent UI's design system.

4. **Connect to Backend Python REST Service using RTK Query**
   - Configure RTK Query API slices to communicate with the Python REST backend.
   - Ensure secure communication and error handling.

5. **Implement AI Assistant Features**
   - Enable message handling and AI assistant interactions.
   - Process user inputs and display assistant responses.

6. **Testing and Deployment**
   - Write unit and integration tests.
   - Prepare the application for deployment and set up CI/CD pipelines.

7. **Final Documentation and README Update**
   - Document the codebase and provide setup instructions. Include details on using pnpm for package management and introducing Fluent UI React components into the project.
   - Update the README with usage guidelines, including commands for package installation and example code for integrating Fluent UI.
 - Encourage contributions by providing guidelines for submitting improvements or new features.

---

---

This README outlines the high-level plan and current status of the AI assistant chat application, incorporating new configurations and components established during recent development efforts.

## Getting Started

To run the application locally, make sure you're prepared with the following steps:

### Important Information

- **Environment Variable Configuration**: We've added support for an environment variable `VITE_DISABLE_STRICT_MODE`. This variable allows you to toggle `React.StrictMode` on or off during development.
  - To disable strict mode, set `VITE_DISABLE_STRICT_MODE=true` in your environment.
  - This is useful for debugging and testing without the extra checks `React.StrictMode` enforces.

- **Launch Configuration**: Updated the launch configuration to use consistent project naming (`app: workspaces-app`). Use this setup in your development environment via VSCode.

- **Initial Component Setup**: The `index.tsx` and `App.tsx` have been set up as entry point and main component, respectively.
  - `index.tsx`: Handles rendering the app entry and activating strict mode based on configuration.
  - `App.tsx`: Currently a placeholder component for the application.

### Installation

Ensure you have `pnpm` installed. Then, run the following command:

```bash
pnpm install
```

This will install all necessary dependencies.

### Running the Development Server

To start the development server, use the following command:

```bash
pnpm dev
```

This will launch the application and watch for any changes.

### Building the Application

To build the application for production, use the following command:

```bash
pnpm build
```

This will create an optimized production build.

### Previewing the Built Application

After building the application, you can preview it using:

```bash
pnpm preview
```

This serves the built application locally for testing.



The following is the proposed folder structure for the AI assistant chat application:

```
/workspaces-app
|-- /public
|   |-- index.html                # HTML entry point
|   |-- favicon.ico               # Application icon
|
|-- /src
|   |-- /assets                  # Static assets (images, fonts, etc.)
|   |-- /components              # Reusable React components
|   |   |-- ChatWindow.tsx       # Main chat interface component
|   |   |-- MessageList.tsx      # Component to display chat messages
|   |   `-- MessageInput.tsx     # Input component for sending messages
|   |
|   |-- /contexts                # Context providers for global state
|   |   `-- ThemeContext.tsx     # Example for theming
|   |
|   |-- /features                # RTK slices and features
|   |   |-- chatSlice.ts         # RTK slice for managing chat state
|   |
|   |-- /hooks                   # Custom React hooks
|   |   `-- useChatEvents.ts     # Hook for handling SSE
|   |
|   |-- /services                # API services and configurations
|   |   |-- api.ts               # RTK Query API setup
|   |   `-- sseClient.ts         # SSE client handling
|   |
|   |-- /styles                  # Styling files
|   |   `-- main.css             # Custom global styles
|   |
|   |-- /utils                   # Utility functions and helpers
|   |   `-- helpers.ts           # General purpose helper functions
|   |
|   `-- App.tsx                  # Main application component
|   `-- index.tsx                # Application entry point
|
|-- package.json                 # Package manifest
|-- tsconfig.json                # TypeScript configuration
|-- README.md                    # Project documentation
```

### Highlights of the Structure:

- **`/public`**: Contains static files like `index.html` and others that do not need to be processed by the build tool.
- **`/src/components`**: Dedicated to the individual UI components of your application.
- **`/src/features`**: Contains Redux slices and features for organizing state management.
- **`/src/hooks`**: A place for custom hooks like those handling SSE interactions.
- **`/src/services`**: Service-related code such as API configuration and SSE client handling.
- **`/src/styles`**: Centralized styling files, which could use CSS, SCSS, or CSS-in-JS solutions.
- **`/src/utils`**: Utility functions and helpers shared across the application.

This structure provides separation of concerns and a clear organization that should make future modifications and additions easier.


This README outlines the high-level plan to guide the development of the AI assistant chat application.