// Copyright (c) Microsoft. All rights reserved.

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentConfig
{
    public object? ToWorkbenchFormat();
    public void Update(object? config);
}
