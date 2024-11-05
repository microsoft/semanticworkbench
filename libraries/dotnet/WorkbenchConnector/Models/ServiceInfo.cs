// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class ServiceInfo<TAgentConfig>(TAgentConfig cfg)
    where TAgentConfig : IAgentConfig, new()
{
    private readonly TAgentConfig _cfg = cfg;

    [JsonPropertyName("assistant_service_id")]
    public string ServiceId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = new();

    [JsonPropertyName("default_config")]
    public object DefaultConfiguration => this._cfg.ToWorkbenchFormat() ?? new();
}
