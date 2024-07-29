// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class DebugInfo : Dictionary<string, object?>
{
    public DebugInfo(string key, object? info)
    {
        this.Add(key, info);
    }
}
