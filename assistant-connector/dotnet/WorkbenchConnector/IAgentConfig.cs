// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;

namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentConfig
{
    public object? ToWorkbenchFormat();
    public void Update(object? config);
}
