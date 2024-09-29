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
