﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class WorkbenchConnector : IDisposable
{
    protected readonly IAgentServiceStorage Storage;
    protected readonly WorkbenchConfig Config = new();
    protected readonly HttpClient HttpClient;
    protected readonly ILogger Log;
    protected readonly Dictionary<string, AgentBase> Agents;

    private Timer? _pingTimer;

    public WorkbenchConnector(
        IConfiguration appConfig,
        IAgentServiceStorage storage,
        ILogger logger)
    {
        appConfig.GetSection("Workbench").Bind(this.Config);

        this.Log = logger;
        this.Storage = storage;
        this.HttpClient = new HttpClient();
        this.HttpClient.BaseAddress = new Uri(this.Config.WorkbenchEndpoint);
        this.Agents = new Dictionary<string, AgentBase>();

        this.Log.LogTrace("Service instance created");
    }

    /// <summary>
    /// Connect the agent service to workbench backend
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Connecting {1} {2} {3}...", this.Config.ConnectorName, this.Config.ConnectorId, this.Config.ConnectorEndpoint);
        #pragma warning disable CS4014 // ping runs in the background without blocking
        this._pingTimer ??= new Timer(_ => this.PingSemanticWorkbenchBackendAsync(cancellationToken), null, 0, 10000);
        #pragma warning restore CS4014

        List<AgentInfo> agents = await this.Storage.GetAllAgentsAsync(cancellationToken).ConfigureAwait(false);
        this.Log.LogInformation("Starting {0} agents", agents.Count);
        foreach (var agent in agents)
        {
            await this.CreateAgentAsync(agent.Id, agent.Name, agent.Config, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Disconnect the agent service from the workbench backend
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task DisconnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Disconnecting {1} {2} ...", this.Config.ConnectorName, this.Config.ConnectorId);
        this._pingTimer?.Dispose();
        this._pingTimer = null;
        return Task.CompletedTask;
    }

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="name">Agent name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public abstract Task CreateAgentAsync(
        string agentId,
        string? name,
        object? configData,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Get agent with the given ID
    /// </summary>
    /// <param name="agentId">Agent ID</param>
    /// <returns>Agent instance</returns>
    public virtual AgentBase? GetAgent(string agentId)
    {
        return this.Agents.GetValueOrDefault(agentId);
    }

    /// <summary>
    /// Delete an agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default)
    {
        var agent = this.GetAgent(agentId);
        if (agent == null) { return; }

        this.Log.LogInformation("Deleting agent '{0}'", agentId.HtmlEncode());
        await agent.StopAsync(cancellationToken).ConfigureAwait(false);
        this.Agents.Remove(agentId);
        await agent.StopAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set a state content, visible in the state inspector.
    /// The content is visibile in the state inspector, on the right side panel.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="content">Content. Markdown and HTML are supported.</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task UpdateAgentConversationInsightAsync(
        string agentId,
        string conversationId,
        Insight insight,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Updating agent '{0}' '{1}' insight", agentId.HtmlEncode(), insight.Id.HtmlEncode());

        var data = new
        {
            state_id = insight.Id,
            @event = "updated",
            state = new
            {
                id = insight.Id,
                data = new
                {
                    content = insight.Content
                },
                json_schema = new { },
                ui_schema = new { }
            }
        };

        string url = Constants.SendAgentConversationInsightsEvent.Path
            .Replace(Constants.SendAgentConversationInsightsEvent.AgentPlaceholder, agentId)
            .Replace(Constants.SendAgentConversationInsightsEvent.ConversationPlaceholder, conversationId);

        await this.SendAsync(HttpMethod.Post, url, data, agentId, "UpdateAgentConversationInsight", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set a temporary agent status within a conversation.
    /// The status is shown inline in the conversation, as a temporary brief message.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="status">Short status description</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SetAgentStatusAsync(
        string agentId,
        string conversationId,
        string status,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Setting agent status in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        var data = new
        {
            status = status,
            active_participant = true
        };

        string url = Constants.SendAgentStatusMessage.Path
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId);

        await this.SendAsync(HttpMethod.Put, url, data, agentId, $"SetAgentStatus[{status}]", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set a temporary agent status within a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="status">Short status description</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ResetAgentStatusAsync(
        string agentId,
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Setting agent status in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        string payload = """
                         {
                           "status": null,
                           "active_participant": true
                         }
                         """;

        var data = JsonSerializer.Deserialize<object>(payload);

        string url = Constants.SendAgentStatusMessage.Path
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId);

        await this.SendAsync(HttpMethod.Put, url, data!, agentId, "ResetAgentStatus", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Send a message from an agent to a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SendMessageAsync(
        string agentId,
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Sending message in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        string url = Constants.SendAgentMessage.Path
            .Replace(Constants.SendAgentMessage.ConversationPlaceholder, conversationId);

        await this.SendAsync(HttpMethod.Post, url, message, agentId, "SendMessage", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get list of files. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task GetFilesAsync(
        string agentId,
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Fetching list of files in conversation '{0}'", conversationId.HtmlEncode());

        string url = Constants.GetConversationFiles.Path
            .Replace(Constants.GetConversationFiles.ConversationPlaceholder, conversationId);

        HttpResponseMessage result = await this.SendAsync(HttpMethod.Get, url, null, agentId, "GetFiles", cancellationToken).ConfigureAwait(false);

        // TODO: parse response and return list

        /*
        {
            "files": [
                {
                    "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                    "created_datetime": "2024-01-12T11:04:38.923626",
                    "updated_datetime": "2024-01-12T11:04:38.923789",
                    "filename": "LICENSE",
                    "current_version": 1,
                    "content_type": "application/octet-stream",
                    "file_size": 1141,
                    "participant_id": "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                    "participant_role": "user",
                    "metadata": {}
                }
            ]
        }
        */
    }

    /// <summary>
    /// Download file. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DownloadFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Downloading file from conversation '{0}'", conversationId.HtmlEncode());

        string url = Constants.ConversationFile.Path
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName);

        HttpResponseMessage result = await this.SendAsync(HttpMethod.Get, url, null, agentId, "DownloadFile", cancellationToken).ConfigureAwait(false);

        // TODO: parse response and return file

        /*
        < HTTP/1.1 200 OK
        < date: Fri, 12 Jan 2024 11:12:23 GMT
        < content-disposition: attachment; filename="LICENSE"
        < content-type: application/octet-stream
        < transfer-encoding: chunked
        <
        ...
         */
    }

    /// <summary>
    /// Upload a file. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task UploadFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting file {0} from a conversation '{1}'", fileName.HtmlEncode(), conversationId.HtmlEncode());

        string url = Constants.UploadConversationFile.Path
            .Replace(Constants.UploadConversationFile.ConversationPlaceholder, conversationId);

        // TODO: include file using multipart/form-data

        await this.SendAsync(HttpMethod.Put, url, null, agentId, "UploadFile", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Delete a file
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting file {0} from a conversation '{1}'", fileName.HtmlEncode(), conversationId.HtmlEncode());

        string url = Constants.ConversationFile.Path
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName);

        await this.SendAsync(HttpMethod.Delete, url, null, agentId, "DeleteFile", cancellationToken).ConfigureAwait(false);
    }

    public virtual async Task PingSemanticWorkbenchBackendAsync(CancellationToken cancellationToken)
    {
        this.Log.LogTrace("Pinging workbench backend");
        string path = Constants.AgentServiceRegistration.Path
            .Replace(Constants.AgentServiceRegistration.Placeholder, this.Config.ConnectorId);

        var data = new
        {
            name = $"{this.Config.ConnectorName} [{this.Config.ConnectorId}]",
            description = this.Config.ConnectorDescription,
            url = this.Config.ConnectorEndpoint,
            online_expires_in_seconds = 20
        };

        await this.SendAsync(HttpMethod.Put, path, data, null, "PingSWBackend",cancellationToken).ConfigureAwait(false);
    }

#region internals ===========================================================================

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._pingTimer?.Dispose();
            this._pingTimer = null;
            this.HttpClient.Dispose();
        }
    }

    protected virtual async Task<HttpResponseMessage> SendAsync(
        HttpMethod method,
        string url,
        object? data,
        string? agentId,
        string description,
        CancellationToken cancellationToken)
    {
        try
        {
            this.Log.LogTrace("Preparing request: {2}", description);
            HttpRequestMessage request = this.PrepareRequest(method, url, data, agentId);
            this.Log.LogTrace("Sending request {0} {1} [{2}]", method, url.HtmlEncode(), description);
            HttpResponseMessage result = await this.HttpClient
                .SendAsync(request, cancellationToken)
                .ConfigureAwait(false);
            request.Dispose();
            return result;
        }
        catch (HttpRequestException e)
        {
            this.Log.LogError("HTTP request failed: {0}. Request: {1} {2} [{3}]", e.Message.HtmlEncode(), method, url.HtmlEncode(), description);
            throw;
        }
        catch (Exception e)
        {
            this.Log.LogError(e, "Unexpected error");
            throw;
        }
    }

    protected virtual HttpRequestMessage PrepareRequest(
        HttpMethod method,
        string url,
        object? data,
        string? agentId)
    {
        HttpRequestMessage request = new(method, url);
        if (Constants.HttpMethodsWithBody.Contains(method))
        {
            request.Content = new StringContent(JsonSerializer.Serialize(data), Encoding.UTF8, "application/json");
        }

        request.Headers.Add(Constants.HeaderServiceId, this.Config.ConnectorId);
        if (!string.IsNullOrEmpty(agentId))
        {
            request.Headers.Add(Constants.HeaderAgentId, agentId);
        }

        return request;
    }

#endregion
}
