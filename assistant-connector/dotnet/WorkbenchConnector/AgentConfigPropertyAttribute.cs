using System;

namespace Microsoft.SemanticWorkbench.Connector;

[AttributeUsage(AttributeTargets.Property, AllowMultiple = true)]
public class AgentConfigPropertyAttribute : Attribute
{
    public string Name { get; }
    public object Value { get; }

    public AgentConfigPropertyAttribute(string name, object value)
    {
        this.Name = name;
        this.Value = value;
    }
}
