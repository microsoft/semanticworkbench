// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentBase
{
    public string Id { get; }
    public AgentInfo ToDataModel();
}
