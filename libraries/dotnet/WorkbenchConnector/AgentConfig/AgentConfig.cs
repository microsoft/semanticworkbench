// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class AgentConfig : IAgentConfig
{
    public AgentConfig()
    {
    }

    public object? ToWorkbenchFormat()
    {
        Dictionary<string, object> result = new();
        Dictionary<string, object> defs = new();
        Dictionary<string, object> properties = new();
        Dictionary<string, object> jsonSchema = new();
        Dictionary<string, object> uiSchema = new();

        foreach (var property in this.GetType().GetProperties())
        {
            var config = new Dictionary<string, object>();
            var attributes = property.GetCustomAttributes<AgentConfigPropertyAttribute>();
            foreach (var attribute in attributes)
            {
                config[attribute.Name] = attribute.Value;
            }

            properties[property.Name] = config;

            if (config.TryGetValue("uischema", out var uiSchemaValue))
            {
                switch (uiSchemaValue)
                {
                    case "textarea":
                        ConfigUtils.UseTextAreaFor(property.Name, uiSchema);
                        break;
                    case "radiobutton":
                        ConfigUtils.UseRadioButtonsFor(property.Name, uiSchema);
                        break;
                    default:
                        break;
                }
            }
        }

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

    public void Update(object? config)
    {
        if (config == null)
        {
            throw new ArgumentException("Empty configuration");
        }

        if (config is not AgentConfig cfg)
        {
            throw new ArgumentException("Incompatible configuration type");
        }

        foreach (var property in this.GetType().GetProperties())
        {
            property.SetValue(this, property.GetValue(cfg));
        }
    }
}
