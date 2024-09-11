// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticWorkbench.Connector;

public static class ConfigUtils
{
    // Use "text area" instead of default "input box"
    public static void UseTextAreaFor(string propertyName, Dictionary<string, object> uiSchema)
    {
        uiSchema[propertyName] = new Dictionary<string, object>
        {
            { "ui:widget", "textarea" }
        };
    }

    // Use "list of radio buttons" instead of default "select box"
    public static void UseRadioButtonsFor(string propertyName, Dictionary<string, object> uiSchema)
    {
        uiSchema[propertyName] = new Dictionary<string, object>
        {
            { "ui:widget", "radio" }
        };
    }
}
