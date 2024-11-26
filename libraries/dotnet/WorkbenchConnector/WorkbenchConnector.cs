// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class WorkbenchConnector<TAgentConfig> : IDisposable
    where TAgentConfig : AgentConfigBase, new()
{
    protected IAgentServiceStorage Storage { get; private set; }
    protected WorkbenchConfig WorkbenchConfig { get; private set; }
    protected TAgentConfig DefaultAgentConfig { get; private set; }
    protected HttpClient HttpClient { get; private set; }
    protected string ConnectorEndpoint { get; private set; } = string.Empty;
    protected ILogger Log { get; private set; }
    protected Dictionary<string, AgentBase<TAgentConfig>> Agents { get; private set; }

    private Timer? _initTimer;
    private Timer? _pingTimer;

    private readonly IServer _httpServer;

    protected WorkbenchConnector(
        WorkbenchConfig? workbenchConfig,
        TAgentConfig? defaultAgentConfig,
        IAgentServiceStorage storage,
        IServer httpServer,
        ILogger logger)
    {
        this._httpServer = httpServer;
        this.WorkbenchConfig = workbenchConfig ?? new();
        this.DefaultAgentConfig = defaultAgentConfig ?? new();

        this.Log = logger;
        this.Storage = storage;
        this.HttpClient = new HttpClient
        {
            BaseAddress = new Uri(this.WorkbenchConfig.WorkbenchEndpoint)
        };
        this.Agents = [];

        this.Log.LogTrace("Service instance created");
    }

    /// <summary>
    /// Get service details and default agent configuration
    /// </summary>
    public virtual ServiceInfo<TAgentConfig> GetServiceInfo()
    {
        return new ServiceInfo<TAgentConfig>(this.DefaultAgentConfig)
        {
            ServiceId = this.WorkbenchConfig.ConnectorId,
            Name = this.WorkbenchConfig.ConnectorName,
            Description = this.WorkbenchConfig.ConnectorDescription,
        };
    }

    /// <summary>
    /// Connect the agent service to workbench backend
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Connecting {ConnectorName} {ConnectorId} to {WorkbenchEndpoint}...",
            this.WorkbenchConfig.ConnectorName, this.WorkbenchConfig.ConnectorId, this.WorkbenchConfig.WorkbenchEndpoint);
#pragma warning disable CS4014 // ping runs in the background without blocking
        this._initTimer ??= new Timer(_ => this.Init(), null, 0, 500);
        this._pingTimer ??= new Timer(_ => this.PingSemanticWorkbenchBackendAsync(cancellationToken), null, Timeout.Infinite, Timeout.Infinite);
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
    public virtual async Task DisconnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Disconnecting {1} {2} ...", this.WorkbenchConfig.ConnectorName, this.WorkbenchConfig.ConnectorId);
        if (this._pingTimer != null)
        {
            await this._pingTimer.DisposeAsync().ConfigureAwait(false);
        }

        this._pingTimer = null;
    }

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="name">Agent name</param>
    /// <param name="configData">Configuration content</param>
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
    public virtual AgentBase<TAgentConfig>? GetAgent(string agentId)
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
    /// The content is visible in the state inspector, on the right side panel.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="insight">Insight content. Markdown and HTML are supported.</param>
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
            .Replace(Constants.SendAgentConversationInsightsEvent.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentConversationInsightsEvent.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Put, url, data, agentId, $"SetAgentStatus[{status}]", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Reset the temporary agent status within a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ResetAgentStatusAsync(
        string agentId,
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Setting agent status in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        const string Payload = """
                               {
                                 "status": null,
                                 "active_participant": true
                               }
                               """;

        var data = JsonSerializer.Deserialize<object>(Payload);

        string url = Constants.SendAgentStatusMessage.Path
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.SendAgentMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.GetConversationFiles.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.UploadConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

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
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Delete, url, null, agentId, "DeleteFile", cancellationToken).ConfigureAwait(false);
    }

    public virtual void DisablePingTimer()
    {
        this._pingTimer?.Change(Timeout.Infinite, Timeout.Infinite);
    }

    public virtual void DisableInitTimer()
    {
        this._initTimer?.Change(Timeout.Infinite, Timeout.Infinite);
    }

    public virtual void EnablePingTimer()
    {
        this._pingTimer?.Change(TimeSpan.FromMilliseconds(PingFrequencyMsecs), TimeSpan.FromMilliseconds(PingFrequencyMsecs));
    }

    public virtual void EnableInitTimer()
    {
        this._initTimer?.Change(TimeSpan.FromMilliseconds(500), TimeSpan.FromMilliseconds(500));
    }

    /// <summary>
    /// Detect the port where the connector is listening and define the value of this.ConnectorEndpoint
    /// which is then passed to the workbench backend for incoming connections.
    /// </summary>
    public virtual void Init()
    {
        this.DisableInitTimer();

        this.Log.LogTrace("Initialization in progress...");

        // If the connector endpoint is ready (to be passed to workbench backend)
        if (!string.IsNullOrWhiteSpace(this.ConnectorEndpoint))
        {
            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
            return;
        }

        // If the connector host is set via configuration, rather than autodetected
        if (!string.IsNullOrWhiteSpace(this.WorkbenchConfig.ConnectorHost))
        {
            this.ConnectorEndpoint = $"{this.WorkbenchConfig.ConnectorHost.TrimEnd('/')}/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}";
            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
            return;
        }

        // Autodetect the port in use and define the connector endpoint
        try
        {
            IServerAddressesFeature? feat = this._httpServer.Features.Get<IServerAddressesFeature>();
            if (feat == null || feat.Addresses.Count == 0)
            {
                this.EnableInitTimer();
                return;
            }

            // Example: http://[::]:64351
            string first = feat.Addresses.First().Replace("[::]", "host", StringComparison.OrdinalIgnoreCase);
            Uri uri = new(first);
            this.ConnectorEndpoint = uri.Port > 0
                ? $"{uri.Scheme}://127.0.0.1:{uri.Port}/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}"
                : $"{uri.Scheme}://127.0.0.1:/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}";

            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
        }
#pragma warning disable CA1031
        catch (Exception e)
        {
            this.Log.LogError(e, "Initialization error: {Message}", e.Message);
            this.EnableInitTimer();
        }
#pragma warning restore CA1031
    }

    public virtual async Task PingSemanticWorkbenchBackendAsync(CancellationToken cancellationToken)
    {
        this.DisablePingTimer();

        try
        {
            string path = Constants.AgentServiceRegistration.Path
                .Replace(Constants.AgentServiceRegistration.Placeholder, this.WorkbenchConfig.ConnectorId, StringComparison.OrdinalIgnoreCase);
            this.Log.LogTrace("Pinging workbench backend at {Path}", path);

            var data = new
            {
                name = $"{this.WorkbenchConfig.ConnectorName} [{this.WorkbenchConfig.ConnectorId}]",
                description = this.WorkbenchConfig.ConnectorDescription,
                url = this.ConnectorEndpoint,
                online_expires_in_seconds = 2 + (int)(PingFrequencyMsecs / 1000)
            };

            await this.SendAsync(HttpMethod.Put, path, data, null, "PingSWBackend", cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            this.EnablePingTimer();
        }
    }

    #region internals ===========================================================================

    private const int PingFrequencyMsecs = 20000;

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
        url = url.TrimStart('/');
        try
        {
            this.Log.LogTrace("Preparing request: {2}", description);
            HttpRequestMessage request = this.PrepareRequest(method, url, data, agentId);
            this.Log.LogTrace("Sending request {Method} {BaseAddress}{Path} [{Description}]", method, this.HttpClient.BaseAddress, url, description);
            this.Log.LogTrace("{0}: {1}", description, ToCurl(this.HttpClient, request, data));
            HttpResponseMessage result = await this.HttpClient
                .SendAsync(request, cancellationToken)
                .ConfigureAwait(false);
            request.Dispose();
            this.Log.LogTrace("Response status code: {StatusCodeInt} {StatusCode}", (int)result.StatusCode, result.StatusCode);

            return result;
        }
        catch (HttpRequestException e)
        {
            this.Log.LogError("HTTP request failed: {Message} [{Error}, {Exception}, Status Code: {StatusCode}]. Request: {Method} {URL} [{RequestDescription}]",
                e.Message.HtmlEncode(), e.HttpRequestError.ToString("G"), e.GetType().FullName, e.StatusCode, method, url, description);
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
            var json = JsonSerializer.Serialize(data);
            request.Content = new StringContent(json, Encoding.UTF8, "application/json");
            this.Log.LogTrace("Request body: {Content}", json);
        }

        request.Headers.Add(Constants.HeaderServiceId, this.WorkbenchConfig.ConnectorId);
        this.Log.LogTrace("Request header: {Content}: {Value}", Constants.HeaderServiceId, this.WorkbenchConfig.ConnectorId);
        if (!string.IsNullOrEmpty(agentId))
        {
            request.Headers.Add(Constants.HeaderAgentId, agentId);
            this.Log.LogTrace("Request header: {Content}: {Value}", Constants.HeaderAgentId, agentId);
        }

        return request;
    }

#pragma warning disable CA1305
    private static string ToCurl(HttpClient httpClient, HttpRequestMessage? request, object? data)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentNullException.ThrowIfNull(request.RequestUri);

        var curl = new StringBuilder("curl -v ");

        foreach (var header in request.Headers)
        {
            foreach (var value in header.Value)
            {
                curl.Append($"-H '{header.Key}: {value}' ");
            }
        }

        if (request.Content?.Headers != null)
        {
            foreach (var header in request.Content.Headers)
            {
                foreach (var value in header.Value)
                {
                    curl.Append($"-H '{header.Key}: {value}' ");
                }
            }
        }

        if (Constants.HttpMethodsWithBody.Contains(request.Method))
        {
            curl.Append($"--data '{JsonSerializer.Serialize(data)}' ");
        }

        curl.Append($"-X {request.Method.Method} '{httpClient.BaseAddress}{request.RequestUri}' ");

        return curl.ToString().TrimEnd();
    }
#pragma warning restore CA1305

    #endregion
}
