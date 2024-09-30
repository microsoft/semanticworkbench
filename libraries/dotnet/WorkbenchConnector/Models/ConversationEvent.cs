// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class ConversationEvent
{
    public class EventData
    {
        [JsonPropertyName("participant")]
        public Participant Participant { get; set; } = new();

        [JsonPropertyName("message")]
        public Message Message { get; set; } = new();
    }

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("conversation_id")]
    public string ConversationId { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public DateTimeOffset Timestamp { get; set; } = DateTimeOffset.MinValue;

    [JsonPropertyName("data")]
    public EventData Data { get; set; } = new();
}
