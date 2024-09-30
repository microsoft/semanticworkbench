// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

public class MyAgentConfig : IAgentConfig
{
    [JsonPropertyName(nameof(this.ReplyToAgents))]
    [JsonPropertyOrder(10)]
    public bool ReplyToAgents { get; set; } = false;

    [JsonPropertyName(nameof(this.CommandsEnabled))]
    [JsonPropertyOrder(20)]
    public bool CommandsEnabled { get; set; } = false;

    [JsonPropertyName(nameof(this.Behavior))]
    [JsonPropertyOrder(30)]
    public string Behavior { get; set; } = "none";

    public void Update(object? config)
    {
        if (config == null)
        {
            throw new ArgumentException("Incompatible or empty configuration");
        }

        if (config is not MyAgentConfig cfg)
        {
            throw new ArgumentException("Incompatible configuration type");
        }

        this.ReplyToAgents = cfg.ReplyToAgents;
        this.CommandsEnabled = cfg.CommandsEnabled;
        this.Behavior = cfg.Behavior;
    }

    public object ToWorkbenchFormat()
    {
        Dictionary<string, object> result = new();
        Dictionary<string, object> defs = new();
        Dictionary<string, object> properties = new();
        Dictionary<string, object> jsonSchema = new();
        Dictionary<string, object> uiSchema = new();

        properties[nameof(this.ReplyToAgents)] = new Dictionary<string, object>
        {
            { "type", "boolean" },
            { "title", "Reply to other assistants in conversations" },
            { "description", "Reply to assistants" },
            { "default", false }
        };

        properties[nameof(this.CommandsEnabled)] = new Dictionary<string, object>
        {
            { "type", "boolean" },
            { "title", "Support commands" },
            { "description", "Support commands, e.g. /say" },
            { "default", false }
        };

        properties[nameof(this.Behavior)] = new Dictionary<string, object>
        {
            { "type", "string" },
            { "default", "echo" },
            { "enum", new[] { "echo", "reverse", "safety check", "markdown sample", "code sample", "json sample", "mermaid sample", "html sample", "music sample", "none" } },
            { "title", "How to reply" },
            { "description", "How to reply to messages, what logic to use." },
        };

        ConfigUtils.UseRadioButtonsFor(nameof(this.Behavior), uiSchema);

        jsonSchema["type"] = "object";
        jsonSchema["title"] = "ConfigStateModel";
        jsonSchema["additionalProperties"] = false;
        jsonSchema["properties"] = properties;
        jsonSchema["$defs"] = defs;

        result["json_schema"] = jsonSchema;
        result["ui_schema"] = uiSchema;
        result["config"] = this;

        return result;
    }
}
