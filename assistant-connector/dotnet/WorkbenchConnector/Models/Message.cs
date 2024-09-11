// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Message
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    // "notice" | "chat" | "note" | "command" | "command-response"
    [JsonPropertyName("message_type")]
    public string MessageType { get; set; } = string.Empty;

    // "text/plain"
    [JsonPropertyName("content_type")]
    public string ContentType { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string? Content { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public DateTimeOffset Timestamp { get; set; }

    [JsonPropertyName("sender")]
    public Sender Sender { get; set; } = new();

    [JsonPropertyName("metadata")]
    public MessageMetadata Metadata { get; set; } = new();

    /// <summary>
    /// Prepare a chat message instance
    /// <note>
    /// Content types:
    /// - text/plain
    /// - text/html
    /// - application/json (requires "json_schema" metadata)
    /// </note>
    /// </summary>
    /// <param name="agentId">Agent ID</param>
    /// <param name="content">Chat content</param>
    /// <param name="debug">Optional debugging data</param>
    /// <param name="contentType">Message content type</param>
    public static Message CreateChatMessage(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = new Message
        {
            Id = Guid.NewGuid().ToString("D"),
            Timestamp = DateTimeOffset.UtcNow,
            MessageType = "chat",
            ContentType = contentType,
            Content = content,
            Sender = new Sender
            {
                Role = "assistant",
                Id = agentId
            }
        };

        if (debug != null)
        {
            result.Metadata.Debug = debug;
        }

        return result;
    }

    public static Message CreateNotice(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "notice";
        return result;
    }

    public static Message CreateNote(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "note";
        return result;
    }

    public static Message CreateCommand(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "command";
        return result;
    }

    public static Message CreateCommandResponse(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "command-response";
        return result;
    }
}
