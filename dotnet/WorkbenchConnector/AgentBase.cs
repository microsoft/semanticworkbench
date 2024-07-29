// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class AgentBase
{
    // Agent instance ID
    public string Id { get; protected set; } = string.Empty;

    // Agent instance name
    public string Name { get; protected set; } = string.Empty;

    // Agent settings
    public IAgentConfig RawConfig { get; protected set; }

    // Simple storage layer to persist agents data
    protected readonly IAgentServiceStorage Storage;

    // Reference to agent service
    protected readonly WorkbenchConnector WorkbenchConnector;

    // Agent logger
    protected readonly ILogger Log;

    /// <summary>
    /// Agent instantiation
    /// </summary>
    /// <param name="workbenchConnector">Semantic Workbench connector</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="log">Agent logger</param>
    public AgentBase(
        WorkbenchConnector workbenchConnector,
        IAgentServiceStorage storage,
        ILogger log)
    {
        this.RawConfig = null!;
        this.WorkbenchConnector = workbenchConnector;
        this.Storage = storage;
        this.Log = log;
    }

    /// <summary>
    /// Convert agent config to a persisten data model
    /// </summary>
    public virtual AgentInfo ToDataModel()
    {
        return new AgentInfo
        {
            Id = this.Id,
            Name = this.Name,
            Config = this.RawConfig,
        };
    }

    /// <summary>
    /// Return default agent configuration
    /// </summary>
    public abstract IAgentConfig GetDefaultConfig();

    /// <summary>
    /// Parse object to agent configuration instance
    /// </summary>
    /// <param name="data">Untyped configuration data</param>
    public abstract IAgentConfig? ParseConfig(object data);

    /// <summary>
    /// Start the agent
    /// </summary>
    public virtual Task StartAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.SaveAgentAsync(this, cancellationToken);
    }

    /// <summary>
    /// Stop the agent
    /// </summary>
    public virtual Task StopAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.DeleteAgentAsync(this, cancellationToken);
    }

    /// <summary>
    /// Update the configuration of an agent instance
    /// </summary>
    /// <param name="config">Configuration data</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>Agent configuration</returns>
    public virtual async Task<IAgentConfig> UpdateAgentConfigAsync(
        IAgentConfig? config,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Updating agent '{0}' config", this.Id);

        this.RawConfig ??= this.GetDefaultConfig();
        config ??= this.GetDefaultConfig();

        this.RawConfig.Update(config);
        await this.Storage.SaveAgentAsync(this, cancellationToken).ConfigureAwait(false);
        return this.RawConfig;
    }

    /// <summary>
    /// Return the list of states in the given conversation.
    /// TODO: Support states with UI
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task<List<Insight>> GetConversationInsightsAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        return this.Storage.GetAllInsightsAsync(this.Id, conversationId, cancellationToken);
    }

    /// <summary>
    /// Notify the workbench about an update of the given state.
    /// States are visible in a conversation, on the right panel.
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="insight">State ID and content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SetConversationInsightAsync(
        string conversationId,
        Insight insight,
        CancellationToken cancellationToken = default)
    {
        await Task.WhenAll([
            this.Storage.SaveInsightAsync(this.Id, conversationId, insight, cancellationToken),
            this.WorkbenchConnector.UpdateAgentConversationInsightAsync(this.Id, conversationId, insight, cancellationToken)
        ]).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a new conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task CreateConversationAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Creating conversation '{0}' on agent '{1}'", conversationId, this.Id);

        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        await Task.WhenAll([
            this.SetConversationInsightAsync(conversation.Id, new Insight("log", "Log", $"Conversation started at {DateTimeOffset.UtcNow}"), cancellationToken),
            this.Storage.SaveConversationAsync(conversation, cancellationToken)
        ]).ConfigureAwait(false);
    }

    /// <summary>
    /// Delete a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task DeleteConversationAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting conversation '{0}' on agent '{1}'", conversationId, this.Id);
        return this.Storage.DeleteConversationAsync(conversationId, this.Id, cancellationToken);
    }

    /// <summary>
    /// Check if a conversation with a given ID exists
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>True if the conversation exists</returns>
    public virtual async Task<bool> ConversationExistsAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Checking if conversation '{0}' on agent '{1}' exists", conversationId, this.Id);
        var conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        return conversation != null;
    }

    /// <summary>
    /// Add a new participant to an existing conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="participant">Participant information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task AddParticipantAsync(
        string conversationId,
        Participant participant,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Adding participant to conversation '{0}' on agent '{1}'", conversationId, this.Id);

        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        conversation.AddParticipant(participant);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove a participant from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="participantCreatedEvent">Participant information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task RemoveParticipantAsync(
        string conversationId,
        Participant participantUpdatedEvent,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Removing participant from conversation '{0}' on agent '{1}'", conversationId, this.Id);

        Conversation? conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        if (conversation == null) { return; }

        conversation.RemoveParticipant(participantUpdatedEvent);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Add a message (received from the backend) to a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} chat message in conversation '{1}' with agent '{2}' from '{3}' '{4}'",
            message.ContentType, conversationId, this.Id, message.Sender.Role, message.Sender.Id);

        // Update the chat history to include the message received
        return this.AddMessageToHistoryAsync(conversationId, message, cancellationToken);
    }

    /// <summary>
    /// Receive a notice, a special type of message.
    /// A notice is a message type for sending short, one-line updates that persist in the chat history
    /// and are displayed differently from regular chat messages.
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveNoticeAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} notice in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType, conversationId, this.Id, message.Sender.Role, message.Sender.Id, message.Content);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a note, a special type of message.
    /// A note is used to display additional information separately from the main conversation.
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveNoteAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} note in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType, conversationId, this.Id, message.Sender.Role, message.Sender.Id, message.Content);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a command, a special type of message
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveCommandAsync(
        string conversationId,
        Command command,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received '{0}' command in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            command.CommandName, conversationId, this.Id, command.Sender.Role, command.Sender.Id, command.Content);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a command response, a special type of message
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveCommandResponseAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} command response in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType, conversationId, this.Id, message.Sender.Role, message.Sender.Id, message.Content);

        return Task.CompletedTask;
    }

    /// <summary>
    /// Remove a message from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="messageCreatedEvent">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting message in conversation '{0}' with agent '{1}', message from '{2}' '{3}'",
            conversationId, this.Id, message.Sender.Role, message.Sender.Id);

        // return this.DeleteMessageFromHistoryAsync(conversationId, message, cancellationToken);
        Conversation? conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        if (conversation == null) { return; }

        conversation.RemoveMessage(message);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Add message to chat history
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task<Conversation> AddMessageToHistoryAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        conversation.AddMessage(message);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
        return conversation;
    }

    // Send a new message to a conversation, communicating with semantic workbench backend
    /// <summary>
    /// Send message to workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task SendTextMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        return this.WorkbenchConnector.SendMessageAsync(this.Id, conversationId, message, cancellationToken);
    }

    /// <summary>
    /// Send a status update to a conversation, communicating with semantic workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="content"></param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task SetAgentStatusAsync(
        string conversationId,
        string content,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogWarning("Change agent '{0}' status in conversation '{1}'", this.Id, conversationId);
        return this.WorkbenchConnector.SetAgentStatusAsync(this.Id, conversationId, content, cancellationToken);
    }

    /// <summary>
    /// Reset the agent status update in a conversation, communicating with semantic workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task ResetAgentStatusAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogWarning("Reset agent '{0}' status in conversation '{1}'", this.Id, conversationId);
        return this.WorkbenchConnector.ResetAgentStatusAsync(this.Id, conversationId, cancellationToken);
    }
}
