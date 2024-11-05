// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class AgentBase<TAgentConfig> : IAgentBase
    where TAgentConfig : AgentConfigBase, new()
{
    // Agent instance ID
    public string Id { get; protected set; } = string.Empty;

    // Agent instance name
    public string Name { get; protected set; } = string.Empty;

    // Agent settings
    public TAgentConfig Config { get; protected set; } = new();

    // Simple storage layer to persist agents data
    protected IAgentServiceStorage Storage { get; private set; }

    // Reference to agent service
    protected WorkbenchConnector<TAgentConfig> WorkbenchConnector { get; private set; }

    // Agent logger
    protected ILogger Log { get; private set; }

    /// <summary>
    /// Agent instantiation
    /// </summary>
    /// <param name="workbenchConnector">Semantic Workbench connector</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="log">Agent logger</param>
    protected AgentBase(
        WorkbenchConnector<TAgentConfig> workbenchConnector,
        IAgentServiceStorage storage,
        ILogger log)
    {
        this.WorkbenchConnector = workbenchConnector;
        this.Storage = storage;
        this.Log = log;
    }

    /// <summary>
    /// Convert agent config to a persistent data model
    /// </summary>
    public virtual AgentInfo ToDataModel()
    {
        return new AgentInfo
        {
            Id = this.Id,
            Name = this.Name,
            Config = this.Config,
        };
    }

    /// <summary>
    /// Parse object to agent configuration instance
    /// </summary>
    /// <param name="data">Untyped configuration data</param>
    public virtual TAgentConfig? ParseConfig(object data)
    {
        return JsonSerializer.Deserialize<TAgentConfig>(JsonSerializer.Serialize(data));
    }

    /// <summary>
    /// Update the configuration of an agent instance
    /// </summary>
    /// <param name="config">Configuration data</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>Agent configuration</returns>
    public virtual async Task<TAgentConfig> UpdateAgentConfigAsync(
        TAgentConfig? config,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Updating agent '{0}' config", this.Id.HtmlEncode());
        this.Config = config ?? new TAgentConfig();
        await this.Storage.SaveAgentAsync(this, cancellationToken).ConfigureAwait(false);
        return this.Config;
    }

    /// <summary>
    /// Start the agent
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task StartAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.SaveAgentAsync(this, cancellationToken);
    }

    /// <summary>
    /// Stop the agent
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task StopAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.DeleteAgentAsync(this, cancellationToken);
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
        this.Log.LogDebug("Creating conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

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
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task DeleteConversationAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());
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
        this.Log.LogDebug("Checking if conversation '{0}' on agent '{1}' exists",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());
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
        this.Log.LogDebug("Adding participant to conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        conversation.AddParticipant(participant);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove a participant from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="participant">Participant information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task RemoveParticipantAsync(
        string conversationId,
        Participant participant,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Removing participant from conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

        Conversation? conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        if (conversation == null) { return; }

        conversation.RemoveParticipant(participant);
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
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode());

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
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

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
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a command, a special type of message
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="command">Command information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveCommandAsync(
        string conversationId,
        Command command,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received '{0}' command in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            command.CommandName.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), command.Sender.Role.HtmlEncode(), command.Sender.Id.HtmlEncode(), command.Content.HtmlEncode());

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
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Remove a message from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting message in conversation '{0}' with agent '{1}', message from '{2}' '{3}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode());

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
        this.Log.LogWarning("Change agent '{0}' status in conversation '{1}'", this.Id.HtmlEncode(), conversationId.HtmlEncode());
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
        this.Log.LogWarning("Reset agent '{0}' status in conversation '{1}'", this.Id.HtmlEncode(), conversationId.HtmlEncode());
        return this.WorkbenchConnector.ResetAgentStatusAsync(this.Id, conversationId, cancellationToken);
    }
}
