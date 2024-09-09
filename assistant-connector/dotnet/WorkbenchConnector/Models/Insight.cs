// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

// TODO: Support states with UI
public class Insight
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("display_name")]
    [JsonPropertyOrder(1)]
    public string DisplayName { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    [JsonPropertyOrder(2)]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    [JsonPropertyOrder(3)]
    public string Content { get; set; } = string.Empty;

    public Insight()
    {
    }

    public Insight(string id, string displayName, string? content, string? description = "")
    {
        this.Id = id;
        this.DisplayName = displayName;
        this.Description = description ?? string.Empty;
        this.Content = content ?? string.Empty;
    }
}
