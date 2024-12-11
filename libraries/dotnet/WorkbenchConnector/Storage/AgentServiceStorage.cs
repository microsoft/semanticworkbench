// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class AgentServiceStorage : IAgentServiceStorage
{
    private static readonly JsonSerializerOptions s_jsonOptions = new() { WriteIndented = true };

    private static readonly char[] s_notSafe =
    [
        '\0', '\n', '\r',
        Path.PathSeparator, // ':' (nix) or ';' (win)
        Path.DirectorySeparatorChar, // '/' (nix) or '\' (win)
        Path.VolumeSeparatorChar, // '/' (nix) or ':' (win)
        Path.AltDirectorySeparatorChar, // '/'
    ];

    private static readonly char[] s_notSafe2 = Path.GetInvalidPathChars();

    private readonly ILogger<AgentServiceStorage> _log;
    private readonly string _path;

    public AgentServiceStorage(
        IConfiguration appConfig,
        ILoggerFactory logFactory)
    {
        this._log = logFactory.CreateLogger<AgentServiceStorage>();

        var connectorId = appConfig.GetSection("Workbench").GetValue<string>("ConnectorId") ?? "undefined";
        var tmpPath = appConfig.GetSection("Workbench").GetValue<string>(
            RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? "StoragePathWindows"
                : "StoragePathLinux") ?? string.Empty;
        this._path = Path.Join(tmpPath, connectorId);

        if (this._path.Contains("$tmp", StringComparison.OrdinalIgnoreCase))
        {
            this._path = this._path.Replace("$tmp", Path.GetTempPath(), StringComparison.OrdinalIgnoreCase);
        }

        this._path = Path.Join(this._path, "agents");

        if (!Directory.Exists(this._path))
        {
            Directory.CreateDirectory(this._path);
        }
    }

    public Task SaveAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default)
    {
        return File.WriteAllTextAsync(this.GetAgentFilename(agent), JsonSerializer.Serialize(agent.ToDataModel(), s_jsonOptions), cancellationToken);
    }

    public Task DeleteAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default)
    {
        File.Delete(this.GetAgentFilename(agent)); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    public Task<List<AgentInfo>> GetAllAgentsAsync(CancellationToken cancellationToken = default)
    {
        return this.GetAllAsync<AgentInfo>("", ".agent.json", cancellationToken);
    }

    public Task SaveConversationAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(conversation);
        var json = JsonSerializer.Serialize(conversation, s_jsonOptions);
        return File.WriteAllTextAsync(filename, json, cancellationToken);
    }

    public async Task<Conversation?> GetConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(agentId: agentId, conversationId: conversationId);
        if (!File.Exists(filename)) { return null; }

        var content = await File.ReadAllTextAsync(filename, cancellationToken).ConfigureAwait(false);
        return JsonSerializer.Deserialize<Conversation>(content);
    }

    public async Task DeleteConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(agentId: agentId, conversationId: conversationId);
        File.Delete(filename); // codeql [cs/path-injection]: safe

        var insights = await this.GetAllInsightsAsync(agentId: agentId, conversationId: conversationId, cancellationToken).ConfigureAwait(false);
        foreach (Insight x in insights)
        {
            await this.DeleteInsightAsync(agentId: agentId, conversationId: conversationId, insightId: x.Id, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
    }

    public Task DeleteConversationAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(conversation);
        File.Delete(filename); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    public Task<List<Insight>> GetAllInsightsAsync(string agentId, string conversationId, CancellationToken cancellationToken = default)
    {
        return this.GetAllAsync<Insight>($"{agentId}.{conversationId}.", ".insight.json", cancellationToken);
    }

    public Task SaveInsightAsync(string agentId, string conversationId, Insight insight, CancellationToken cancellationToken = default)
    {
        var filename = this.GetInsightFilename(agentId: agentId, conversationId: conversationId, insightId: insight.Id);
        return File.WriteAllTextAsync(filename, JsonSerializer.Serialize(insight, s_jsonOptions), cancellationToken);
    }

    public Task DeleteInsightAsync(string agentId, string conversationId, string insightId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetInsightFilename(agentId: agentId, conversationId: conversationId, insightId: insightId);
        File.Delete(filename); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    private async Task<List<T>> GetAllAsync<T>(string prefix, string suffix, CancellationToken cancellationToken = default)
    {
        this._log.LogTrace("Searching all files with prefix '{0}' and suffix '{1}'",
            prefix.HtmlEncode(), suffix.HtmlEncode());

        var result = new List<T>();
        string[] fileEntries = Directory.GetFiles(this._path);
        foreach (string filePath in fileEntries)
        {
            var filename = Path.GetFileName(filePath);
            if (!filename.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) { continue; }

            if (!filename.EndsWith(suffix, StringComparison.OrdinalIgnoreCase)) { continue; }

            var content = await File.ReadAllTextAsync(filePath, cancellationToken).ConfigureAwait(false);
            if (string.IsNullOrEmpty(content)) { continue; }

            result.Add(JsonSerializer.Deserialize<T>(content)!);
        }

        this._log.LogTrace("Files found: {0}", result.Count);

        return result;
    }

    private string GetAgentFilename(IAgentBase agent)
    {
        EnsureSafe(agent.Id);
        return Path.Join(this._path, $"{agent.Id}.agent.json");
    }

    private string GetConversationFilename(Conversation conversation)
    {
        return this.GetConversationFilename(conversation.AgentId, conversation.Id);
    }

    private string GetConversationFilename(string agentId, string conversationId)
    {
        EnsureSafe(agentId);
        EnsureSafe(conversationId);
        return Path.Join(this._path, $"{agentId}.{conversationId}.conversation.json");
    }

    private string GetInsightFilename(string agentId, string conversationId, string insightId)
    {
        EnsureSafe(agentId);
        EnsureSafe(conversationId);
        EnsureSafe(insightId);
        return Path.Join(this._path, $"{agentId}.{conversationId}.{insightId}.insight.json");
    }

    private static void EnsureSafe(string input)
    {
        if (input.IndexOfAny(s_notSafe) < 0 && input.IndexOfAny(s_notSafe2) < 0) { return; }

        throw new ArgumentException("The file or path value contains invalid chars");
    }
}
