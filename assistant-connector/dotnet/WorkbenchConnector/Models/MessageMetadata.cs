// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class MessageMetadata
{
    [JsonPropertyName("attribution")]
    public string Attribution { get; set; } = string.Empty;

    [JsonPropertyName("debug")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Debug { get; set; } = null;
}
