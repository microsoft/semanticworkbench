// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Sender
{
    [JsonPropertyName("participant_role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("participant_id")]
    public string Id { get; set; } = string.Empty;
}
