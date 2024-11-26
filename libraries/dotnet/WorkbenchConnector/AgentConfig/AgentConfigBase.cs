// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Reflection;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public abstract class AgentConfigBase
{
    public object ToWorkbenchFormat()
    {
        Dictionary<string, object> result = [];
        Dictionary<string, object> defs = [];
        Dictionary<string, object> properties = [];
        Dictionary<string, object> jsonSchema = [];
        Dictionary<string, object> uiSchema = [];

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
}
