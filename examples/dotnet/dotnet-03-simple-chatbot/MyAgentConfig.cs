// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Microsoft.SemanticWorkbench.Connector;

namespace AgentExample;

public class MyAgentConfig : AgentConfig
{
    [JsonPropertyName(nameof(this.ReplyToAgents))]
    [JsonPropertyOrder(10)]
    [AgentConfigProperty("type", "boolean")]
    [AgentConfigProperty("title", "Reply to other assistants in conversations")]
    [AgentConfigProperty("description", "Reply to assistants")]
    [AgentConfigProperty("default", false)]
    public bool ReplyToAgents { get; set; } = false;

    [JsonPropertyName(nameof(this.CommandsEnabled))]
    [JsonPropertyOrder(20)]
    [AgentConfigProperty("type", "boolean")]
    [AgentConfigProperty("title", "Support commands")]
    [AgentConfigProperty("description", "Support commands, e.g. /say")]
    [AgentConfigProperty("default", false)]
    public bool CommandsEnabled { get; set; } = false;

    [JsonPropertyName(nameof(this.MaxMessagesCount))]
    [JsonPropertyOrder(30)]
    [AgentConfigProperty("type", "integer")]
    [AgentConfigProperty("title", "Max conversation messages")]
    [AgentConfigProperty("description", "How many messages to answer in a conversation before ending and stopping replies.")]
    [AgentConfigProperty("minimum", 1)]
    [AgentConfigProperty("maximum", int.MaxValue)]
    [AgentConfigProperty("default", 100)]
    public int MaxMessagesCount { get; set; } = 100;

    [JsonPropertyName(nameof(this.Temperature))]
    [JsonPropertyOrder(40)]
    [AgentConfigProperty("type", "number")]
    [AgentConfigProperty("title", "LLM temperature")]
    [AgentConfigProperty("description", "The temperature value ranges from 0 to 1. Lower values indicate greater determinism and higher values indicate more randomness.")]
    [AgentConfigProperty("minimum", 0.0)]
    [AgentConfigProperty("maximum", 1.0)]
    [AgentConfigProperty("default", 0.0)]
    public double Temperature { get; set; } = 0.0;

    [JsonPropertyName(nameof(this.NucleusSampling))]
    [JsonPropertyOrder(50)]
    [AgentConfigProperty("type", "number")]
    [AgentConfigProperty("title", "LLM nucleus sampling")]
    [AgentConfigProperty("description", "Nucleus sampling probability ranges from 0 to 1. Lower values result in more deterministic outputs by limiting the choice to the most probable words, and higher values allow for more randomness by including a larger set of potential words.")]
    [AgentConfigProperty("minimum", 0.0)]
    [AgentConfigProperty("maximum", 1.0)]
    [AgentConfigProperty("default", 1.0)]
    public double NucleusSampling { get; set; } = 1.0;

    [JsonPropertyName(nameof(this.LLMProvider))]
    [JsonPropertyOrder(60)]
    [AgentConfigProperty("type", "string")]
    [AgentConfigProperty("default", "openai")]
    [AgentConfigProperty("enum", new[] { "openai", "azure-openai" })]
    [AgentConfigProperty("title", "LLM provider")]
    [AgentConfigProperty("description", "AI service providing the LLM.")]
    [AgentConfigProperty("uischema", "radiobutton")]
    public string LLMProvider { get; set; } = "openai";

    [JsonPropertyName(nameof(this.ModelName))]
    [JsonPropertyOrder(80)]
    [AgentConfigProperty("type", "string")]
    [AgentConfigProperty("title", "OpenAI Model (or Azure Deployment)")]
    [AgentConfigProperty("description", "Model used to generate text.")]
    [AgentConfigProperty("maxLength", 256)]
    [AgentConfigProperty("default", "GPT-4o")]
    public string ModelName { get; set; } = "gpt-4o";
}
