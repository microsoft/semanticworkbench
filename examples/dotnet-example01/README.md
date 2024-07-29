# Using Semantic Workbench with .NET Agents

This project provides an example of testing your agent within the **Semantic Workbench**.

## Project Overview

The sample project utilizes the `WorkbenchConnector` library, enabling you to focus on agent development and testing.

Semantic Workbench allows mixing agents from different frameworks and multiple instances of the same agent. The connector can manage multiple agent instances if needed, or you can work with a single instance if preferred.
To integrate agents developed with other frameworks, we recommend isolating each agent type with a dedicated web service, ie a dedicated project.

## Project Structure

Project Structure

1. `appsettings.json`:
    * Purpose: standard .NET configuration file.
    * Key Points:
        * Contains default values, in particular the ports used.
        * Optionally create `appsettings.development.json` for custom settings.
2. `MyAgentConfig.cs`:
   * Purpose: contains your agent settings.
   * Key Points:
     * Extend `IAgentConfig` to integrate with the workbench connector.
     * Implement `ToWorkbenchFormat()` to visualize and edit configurations in the Semantic Workbench UI.
3. `MyAgent.cs`:
    * Purpose: contains your agent logic.
    * Key Points:
      * Extend `AgentBase`.
      * Implement essential methods:
        * `ReceiveMessageAsync()`: **handles incoming messages using intent detection, plugins, RAG, etc.**
        * `GetDefaultConfig()`: provides default settings for new agent instances.
        * `ParseConfig()`: deserializes a generic object into MyAgentConfig.
        * **You can override default implementation for additional customization.**
4. `MyWorkbenchConnector.cs`:
    * Purpose: custom instance of WorkbenchConnector.
    * Key Points:
      * **Contains code to create an instance of your agent class**.
      * **You can override default implementation for additional customization.**
5. `Program.cs`:
    * Purpose: sets up configuration, dependencies using .NET Dependency Injection and starts services.
    * Key Points:
        * **Starts a web service** to enable communication with Semantic Workbench.
        * **Starts an instance of WorkbenchConnector** for agent communication.
