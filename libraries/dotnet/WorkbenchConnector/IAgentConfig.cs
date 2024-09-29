// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentConfig
{
    public object? ToWorkbenchFormat();
    public void Update(object? config);
}
