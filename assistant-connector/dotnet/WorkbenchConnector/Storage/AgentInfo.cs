// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class AgentInfo
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    [JsonPropertyOrder(1)]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("config")]
    [JsonPropertyOrder(2)]
    public object Config { get; set; } = null!;
}
