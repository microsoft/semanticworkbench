// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample02;

public sealed class MyWorkbenchConnector : WorkbenchConnector
{
    private readonly MyAgentConfig _defaultAgentConfig = new();
    private readonly IServiceProvider _sp;

    public MyWorkbenchConnector(
        IServiceProvider sp,
        IConfiguration appConfig,
        IAgentServiceStorage storage,
        ILoggerFactory? loggerFactory = null)
        : base(appConfig, storage, loggerFactory?.CreateLogger<MyWorkbenchConnector>() ?? new NullLogger<MyWorkbenchConnector>())
    {
        appConfig.GetSection("Agent").Bind(this._defaultAgentConfig);
        this._sp = sp;
    }

    /// <inheritdoc />
    public override async Task CreateAgentAsync(
        string agentId,
        string? name,
        object? configData,
        CancellationToken cancellationToken = default)
    {
        if (this.GetAgent(agentId) != null) { return; }

        this.Log.LogDebug("Creating agent '{0}'", agentId);

        MyAgentConfig config = this._defaultAgentConfig;
        if (configData != null)
        {
            var newCfg = JsonSerializer.Deserialize<MyAgentConfig>(JsonSerializer.Serialize(configData));
            if (newCfg != null) { config = newCfg; }
        }

        // Instantiate using .NET Service Provider so that dependencies are automatically injected
        var agent = ActivatorUtilities.CreateInstance<MyAgent>(this._sp, agentId, name ?? agentId, config);

        await agent.StartAsync(cancellationToken).ConfigureAwait(false);
        this.Agents.TryAdd(agentId, agent);
    }
}
