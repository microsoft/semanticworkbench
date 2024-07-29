// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample01;

public class MyAgent : AgentBase
{
    // Agent settings
    public MyAgentConfig Config
    {
        get { return (MyAgentConfig)this.RawConfig; }
        private set { this.RawConfig = value; }
    }

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="agentName">Agent name</param>
    /// <param name="agentConfig">Agent configuration</param>
    /// <param name="workbenchConnector">Service containing the agent, used to communicate with Workbench backend</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="loggerFactory">App logger factory</param>
    public MyAgent(
        string agentId,
        string agentName,
        MyAgentConfig? agentConfig,
        WorkbenchConnector workbenchConnector,
        IAgentServiceStorage storage,
        ILoggerFactory? loggerFactory = null)
        : base(
            workbenchConnector,
            storage,
            loggerFactory?.CreateLogger<MyAgent>() ?? new NullLogger<MyAgent>())
    {
        this.Id = agentId;
        this.Name = agentName;
        this.Config = agentConfig ?? new MyAgentConfig();
    }

    /// <inheritdoc />
    public override IAgentConfig GetDefaultConfig()
    {
        return new MyAgentConfig();
    }

    /// <inheritdoc />
    public override IAgentConfig? ParseConfig(object data)
    {
        return JsonSerializer.Deserialize<MyAgentConfig>(JsonSerializer.Serialize(data));
    }

    /// <inheritdoc />
    public override async Task ReceiveCommandAsync(
        string conversationId,
        Command command,
        CancellationToken cancellationToken = default)
    {
        // Check if commands are enabled
        if (!this.Config.CommandsEnabled) { return; }

        // Check if we're replying to other agents
        if (!this.Config.ReplyToAgents && command.Sender.Role == "assistant") { return; }

        // Support only the "say" command
        if (command.CommandName.ToLowerInvariant() != "say") { return; }

        // Update the chat history to include the message received
        await base.AddMessageToHistoryAsync(conversationId, command, cancellationToken).ConfigureAwait(false);

        // Create the answer content. CommandParams contains the message to send back.
        var answer = Message.CreateChatMessage(this.Id, command.CommandParams);

        // Update the chat history to include the outgoing message
        await this.AddMessageToHistoryAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);

        // Send the message to workbench backend
        await this.SendTextMessageAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override async Task ReceiveMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Show some status while working...
            await this.SetAgentStatusAsync(conversationId, "Thinking...", cancellationToken).ConfigureAwait(false);

            // Fake delay, to show the status in the chat
            await Task.Delay(TimeSpan.FromSeconds(1), cancellationToken).ConfigureAwait(false);

            // Update the chat history to include the message received
            await base.AddMessageToHistoryAsync(conversationId, message, cancellationToken).ConfigureAwait(false);

            // Check if we're replying to other agents
            if (!this.Config.ReplyToAgents && message.Sender.Role == "assistant") { return; }

            // Ignore empty messages
            if (string.IsNullOrWhiteSpace(message.Content)) { return; }

            // Create the answer content
            var answer = Message.CreateChatMessage(this.Id, "echo: "+ message.Content);

            // Update the chat history to include the outgoing message
            await this.AddMessageToHistoryAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);

            // Send the message to workbench backend
            await this.SendTextMessageAsync(conversationId, answer, cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            // Remove the "Thinking..." status
            await this.ResetAgentStatusAsync(conversationId, cancellationToken).ConfigureAwait(false);
        }
    }
}
