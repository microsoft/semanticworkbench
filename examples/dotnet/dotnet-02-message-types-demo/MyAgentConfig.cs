// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

public class MyAgentConfig : AgentConfig
{
    [JsonPropertyName(nameof(this.ReplyToAgents))]
    [JsonPropertyOrder(10)]
    [AgentConfigProperty("type", "boolean")]
    [AgentConfigProperty("title", "Reply to other assistants in conversations")]
    [AgentConfigProperty("description", "Reply to assistants")]
    [AgentConfigProperty("default", false)]
    public bool ReplyToAgents { get; set; } = false;

    [JsonPropertyName(nameof(this.CommandsEnabled))]
    [JsonPropertyOrder(20)]
    [AgentConfigProperty("type", "boolean")]
    [AgentConfigProperty("title", "Support commands")]
    [AgentConfigProperty("description", "Support commands, e.g. /say")]
    [AgentConfigProperty("default", false)]
    public bool CommandsEnabled { get; set; } = false;

    [JsonPropertyName(nameof(this.Behavior))]
    [JsonPropertyOrder(30)]
    [AgentConfigProperty("type", "string")]
    [AgentConfigProperty("default", "echo")]
    [AgentConfigProperty("enum", new[] { "echo", "reverse", "safety check", "markdown sample", "code sample", "json sample", "mermaid sample", "html sample", "music sample", "none" })]
    [AgentConfigProperty("title", "How to reply")]
    [AgentConfigProperty("description", "How to reply to messages, what logic to use.")]
    [AgentConfigProperty("uischema", "radiobutton")]
    public string Behavior { get; set; } = "none";
}
