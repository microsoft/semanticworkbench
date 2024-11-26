// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Primitives;

namespace Microsoft.SemanticWorkbench.Connector;

public static class Webservice
{
    // Used for logging
    private sealed class SemanticWorkbenchWebservice
    {
    }

    public static WorkbenchConnector<TAgentConfig> UseAgentWebservice<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix, bool enableCatchAll = false)
        where TAgentConfig : AgentConfigBase, new()
    {
        WorkbenchConnector<TAgentConfig>? workbenchConnector = builder.ServiceProvider.GetService<WorkbenchConnector<TAgentConfig>>();
        if (workbenchConnector == null)
        {
            throw new InvalidOperationException("Unable to create instance of " + nameof(WorkbenchConnector<TAgentConfig>));
        }

        builder
            .UseFetchServiceInfo<TAgentConfig>(prefix)
            .UseCreateAgentEndpoint<TAgentConfig>(prefix)
            .UseDeleteAgentEndpoint<TAgentConfig>(prefix)
            .UseFetchAgentConfigEndpoint<TAgentConfig>(prefix)
            .UseSaveAgentConfigEndpoint<TAgentConfig>(prefix)
            .UseCreateConversationEndpoint<TAgentConfig>(prefix)
            .UseDeleteConversationEndpoint<TAgentConfig>(prefix)
            .UseFetchConversationStatesEndpoint<TAgentConfig>(prefix)
            .UseFetchConversationInsightEndpoint<TAgentConfig>(prefix)
            .UseCreateConversationEventEndpoint<TAgentConfig>(prefix);

        if (enableCatchAll)
        {
            builder.UseCatchAllEndpoint(prefix);
        }

        return workbenchConnector;
    }

    // Return service details and default agent configuration
    public static IEndpointRouteBuilder UseFetchServiceInfo<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/", (
            [FromServicesAttribute] WorkbenchConnector<TAgentConfig> workbenchConnector,
            [FromServices] ILogger<SemanticWorkbenchWebservice> log) =>
        {
            var result = workbenchConnector.GetServiceInfo();
            return Results.Json(result);
        });

        return builder;
    }

    // Create new agent instance
    public static IEndpointRouteBuilder UseCreateAgentEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}",
                async (
                    [FromRoute] string agentId,
                    [FromForm(Name = "assistant")] string data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    string? name = agentId;
                    Dictionary<string, string>? settings = JsonSerializer.Deserialize<Dictionary<string, string>>(data);
                    settings?.TryGetValue("assistant_name", out name);

                    log.LogDebug("Received request to create/update agent instance '{0}', name '{1}'",
                        agentId.HtmlEncode(), name.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null)
                    {
                        await workbenchConnector.CreateAgentAsync(agentId, name, null, cancellationToken)
                            .ConfigureAwait(false);
                    }

                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Delete agent instance
    public static IEndpointRouteBuilder UseDeleteAgentEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapDelete(prefix + "/{agentId}",
            async (
                [FromRoute] string agentId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to deleting agent instance '{0}'", agentId.HtmlEncode());
                await workbenchConnector.DeleteAgentAsync(agentId, cancellationToken).ConfigureAwait(false);
                return Results.Ok();
            });

        return builder;
    }

    // Fetch agent configuration
    public static IEndpointRouteBuilder UseFetchAgentConfigEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/config",
            (
                [FromRoute] string agentId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' configuration", agentId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null)
                {
                    return Results.NotFound("Agent Not Found");
                }

                return Results.Json(agent.Config.ToWorkbenchFormat());
            });

        return builder;
    }

    // Save agent configuration
    public static IEndpointRouteBuilder UseSaveAgentConfigEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}/config",
                async (
                    [FromRoute] string agentId,
                    [FromBody] Dictionary<string, object> data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to update agent '{0}' configuration", agentId.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    var config = agent.ParseConfig(data["config"]);
                    AgentConfigBase newConfig =
                        await agent.UpdateAgentConfigAsync(config, cancellationToken).ConfigureAwait(false);

                    var tmp = workbenchConnector.GetAgent(agentId);

                    return Results.Json(newConfig.ToWorkbenchFormat());
                })
            .DisableAntiforgery();

        return builder;
    }

    // Create new conversation
    private static IEndpointRouteBuilder UseCreateConversationEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}/conversations/{conversationId}",
                async (
                    [FromRoute] string agentId,
                    [FromRoute] string conversationId,
                    [FromForm(Name = "conversation")] string data, // e.g. conversation={"id":"34460523-d2be-4388-837d-bda92282ffde"}
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to create conversation '{0}' on agent '{1}'",
                        conversationId.HtmlEncode(), agentId.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    await agent.CreateConversationAsync(conversationId, cancellationToken).ConfigureAwait(false);
                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Fetch conversation states
    public static IEndpointRouteBuilder UseFetchConversationStatesEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/conversations/{conversationId}/states",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' conversation '{1}' states",
                    agentId.HtmlEncode(), conversationId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.NotFound("Conversation Not Found"); }

                if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                {
                    return Results.NotFound("Conversation Not Found");
                }

                List<Insight> states = await agent.GetConversationInsightsAsync(conversationId, cancellationToken).ConfigureAwait(false);

                if (states.Count == 0)
                {
                    // Special case required by UI bug
                    var result = new
                    {
                        states = new[]
                        {
                            new Insight
                            {
                                Id = "__none",
                                DisplayName = "Assistant Info",
                                Description = $"""
                                               Agent ID: **{agent.Id}**

                                               Name: **{agent.Name}**

                                               Config: **{agent.Config}**
                                               end of description
                                               """,
                                Content = $"""
                                           Agent ID: **{agent.Id}**

                                           Name: **{agent.Name}**

                                           Config: **{agent.Config}**
                                           end of content
                                           """
                            }
                        }
                    };
                    return Results.Json(result);
                }
                else
                {
                    var result = new
                    {
                        states = states.Select(x => new Insight { Id = x.Id, DisplayName = x.DisplayName, Description = x.Description })
                    };
                    return Results.Json(result);
                }
            });

        return builder;
    }

    // Fetch conversation states
    public static IEndpointRouteBuilder UseFetchConversationInsightEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/conversations/{conversationId}/states/{insightId}",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromRoute] string insightId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' conversation '{1}' insight '{2}'",
                    agentId.HtmlEncode(), conversationId.HtmlEncode(), insightId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.NotFound("Agent Not Found"); }

                if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                {
                    return Results.NotFound("Conversation Not Found");
                }

                var insights = await agent.GetConversationInsightsAsync(conversationId, cancellationToken).ConfigureAwait(false);
                Insight? insight = insights.FirstOrDefault(x => x.Id == insightId);

                if (insight == null)
                {
                    // Special case required by UI bug
                    if (insightId == "__none")
                    {
                        return Results.Json(new
                        {
                            id = insightId,
                            data = new { content = string.Empty },
                            json_schema = (object)null!,
                            ui_schema = (object)null!
                        });
                    }

                    return Results.NotFound($"State '{insightId}' Not Found");
                }

                // TODO: support schemas
                var result = new
                {
                    id = insightId,
                    data = new
                    {
                        content = insight.Content
                    },
                    json_schema = (object)null!,
                    ui_schema = (object)null!
                };

                return Results.Json(result);
            });

        return builder;
    }

    // New conversation event
    private static IEndpointRouteBuilder UseCreateConversationEventEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPost(prefix + "/{agentId}/conversations/{conversationId}/events",
                async (
                    [FromRoute] string agentId,
                    [FromRoute] string conversationId,
                    [FromBody] Dictionary<string, object>? data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to process new event for agent '{0}' on conversation '{1}'",
                        agentId.HtmlEncode(), conversationId.HtmlEncode());

                    if (data == null || !data.TryGetValue("event", out object? eventType))
                    {
                        log.LogError("Event payload doesn't contain an 'event' property");
                        return Results.BadRequest("Event payload doesn't contain an 'event' property");
                    }

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                    {
                        return Results.NotFound("Conversation Not Found");
                    }

                    var json = JsonSerializer.Serialize(data);
                    log.LogDebug("Agent '{0}', conversation '{1}', Event '{2}'",
                        agentId.HtmlEncode(), conversationId.HtmlEncode(), eventType.HtmlEncode());
                    switch (eventType.ToString())
                    {
                        case "participant.created":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x?.Data.Participant == null) { break; }

                            await agent.AddParticipantAsync(conversationId, x.Data.Participant, cancellationToken).ConfigureAwait(false);
                            break;
                        }

                        case "participant.updated":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x?.Data.Participant == null) { break; }

                            if (x is { Data.Participant.ActiveParticipant: false })
                            {
                                await agent.RemoveParticipantAsync(conversationId, x.Data.Participant, cancellationToken).ConfigureAwait(false);
                            }

                            break;
                        }

                        case "message.created":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x == null) { break; }

                            // Ignore messages sent from the agent itself
                            var message = x.Data.Message;
                            if (message.Sender.Role == "assistant" && message.Sender.Id == agentId) { break; }

                            // Ignore empty messages
                            if (string.IsNullOrWhiteSpace(message.Content)) { break; }

                            switch (message.MessageType)
                            {
                                case "chat":
                                    await agent.ReceiveMessageAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "notice":
                                    await agent.ReceiveNoticeAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "note":
                                    await agent.ReceiveNoteAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "command":
                                    var command = new Command(message);
                                    await agent.ReceiveCommandAsync(conversationId, command, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "command-response":
                                    await agent.ReceiveCommandResponseAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                default:
                                    log.LogInformation("{0}: {1}", message.MessageType.HtmlEncode(),
                                        message.Content.HtmlEncode());
                                    log.LogWarning("Agent '{0}', conversation '{1}', Message type '{2}' ignored",
                                        agentId.HtmlEncode(), conversationId.HtmlEncode(),
                                        message.MessageType.HtmlEncode());
                                    break;
                            }

                            break;
                        }

                        case "message.deleted":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x == null) { break; }

                            await agent.DeleteMessageAsync(conversationId, x.Data.Message, cancellationToken).ConfigureAwait(false);
                            break;
                        }

                        case "assistant.state.created": // TODO
                        case "assistant.state.updated": // TODO
                        case "file.created": // TODO
                        case "file.deleted": // TODO
                            /*
                            {
                               "event":            "assistant.state.created",
                                "id":              "ded0986ca0824e109e5bad8593b5fb1f",
                                "correlation_id":  "4358b84cffec4255b41be26fbf6d7829",
                                "conversation_id": "d7896b39-ad3f-4a10-a595-a7e47f6735b0",
                                "timestamp":       "2024-01-12T23:08:05.689296",
                                "data": {
                                    "assistant_id":    "69b841ff-909c-4fd7-b364-f5f962d5f021",
                                    "state_id":        "state01",
                                    "conversation_id": "d7896b39-ad3f-4a10-a595-a7e47f6735b0"
                                }
                            }

                           {
                                "event":           "assistant.state.updated",
                                "id":              "9ea3f9e2923045599f3ecfdbb07713b2",
                                "correlation_id":  "26c74d31a35b4a2aa301720af2615196",
                                "conversation_id": "483f6253-b5e1-478a-ac9e-4d1a58499c9d",
                                "timestamp":       "2024-11-26T19:01:54.446203Z",
                                "data": {
                                    "assistant_id": "9e58298d-dbe4-4ed3-bfdf-422d1c275de4",
                                    "state_id": "history",
                                    "conversation_id": "483f6253-b5e1-478a-ac9e-4d1a58499c9d"
                                }
                           }

                           {
                                "event":           "file.created",
                                "id":              "9b7ba8b35699482bbe368023796a978d",
                                "correlation_id":  "40877ed10f104090a9996fbe9dd6d716",
                                "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                "timestamp":       "2024-01-12T10:51:16.847854",
                                "data":
                                {
                                    "file":
                                    {
                                        "conversation_id":  "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                        "created_datetime": "2024-01-12T10:51:16.845539Z",
                                        "updated_datetime": "2024-01-12T10:51:16.846093Z",
                                        "filename":         "LICENSE",
                                        "current_version":  1,
                                        "content_type":     "application/octet-stream",
                                        "file_size":        1141,
                                        "participant_id":   "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                                        "participant_role": "user",
                                        "metadata": {}
                                    }
                                }
                            }

                            {
                                "event":           "file.deleted",
                                "id":              "75a3c347d7a644708548065098fa1b0b",
                                "correlation_id":  "7e2aa0f64dc140dbb82a68c50c2f3461",
                                "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                "timestamp":       "2024-07-28T10:55:51.257584",
                                "data": {
                                    "file": {
                                        "conversation_id":  "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                        "created_datetime": "2024-07-28T10:51:16.845539",
                                        "updated_datetime": "2024-07-28T10:51:16.846093",
                                        "filename":         "LICENSE",
                                        "current_version":  1,
                                        "content_type":     "application/octet-stream",
                                        "file_size":        1141,
                                        "participant_id":   "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                                        "participant_role": "user",
                                        "metadata": {}
                                    }
                                }
                            }
                            */
                            log.LogInformation("Event type '{0}' not supported [TODO]", eventType.HtmlEncode());
                            break;

                        default:
                            log.LogWarning("Unknown event type '{0}' not supported", eventType.HtmlEncode());
                            log.LogTrace(json);
                            break;
                    }

                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Delete conversation
    public static IEndpointRouteBuilder UseDeleteConversationEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapDelete(prefix + "/{agentId}/conversations/{conversationId}",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to delete conversation '{0}' on agent instance '{1}'",
                    conversationId.HtmlEncode(), agentId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.Ok(); }

                await agent.DeleteConversationAsync(conversationId, cancellationToken).ConfigureAwait(false);

                return Results.Ok();
            });

        return builder;
    }

    // Catch all endpoint
    private static IEndpointRouteBuilder UseCatchAllEndpoint(
        this IEndpointRouteBuilder builder, string prefix)
    {
        builder.Map(prefix + "/{*catchAll}", async (
            HttpContext context,
            ILogger<SemanticWorkbenchWebservice> log) =>
        {
            context.Request.EnableBuffering();

            // Read headers
            StringBuilder headersStringBuilder = new();
            foreach (KeyValuePair<string, StringValues> header in context.Request.Headers)
            {
                headersStringBuilder.AppendLine(CultureInfo.InvariantCulture, $"{header.Key}: {header.Value}");
            }

            // Read body
            using StreamReader reader = new(context.Request.Body, leaveOpen: true);
            string requestBody = await reader.ReadToEndAsync().ConfigureAwait(false);
            context.Request.Body.Position = 0;

            log.LogWarning("Unknown request: {0} Path: {1}", context.Request.Method, context.Request.Path.HtmlEncode());

            string? query = context.Request.QueryString.Value;
            if (!string.IsNullOrEmpty(query)) { log.LogDebug("Query: {0}", context.Request.QueryString.Value.HtmlEncode()); }

            log.LogDebug("Headers: {0}", headersStringBuilder.HtmlEncode());
            log.LogDebug("Body: {0}", requestBody.HtmlEncode());

            return Results.NotFound("Request not supported");
        });

        return builder;
    }
}
