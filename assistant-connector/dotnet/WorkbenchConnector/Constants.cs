// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticWorkbench.Connector;

public static class Constants
{
    // Unique service ID
    public const string HeaderServiceId = "X-Assistant-Service-ID";

    // Agent ID
    public const string HeaderAgentId = "X-Assistant-ID";

    // HTTP methods
    public static readonly HttpMethod[] HttpMethodsWithBody = [HttpMethod.Post, HttpMethod.Put, HttpMethod.Patch];

    // Registering the multi-agent service into the workbench connector
    public static class AgentServiceRegistration
    {
        public const string Placeholder = "{assistant_service_id}";
        public const string Path = "/assistant-service-registrations/{assistant_service_id}";
    }

    // Sending a message into an existing conversation
    public static class SendAgentMessage
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/messages";
    }

    // Sending a temporary status to show inline in a conversation, before sending a message
    public static class SendAgentStatusMessage
    {
        public const string AgentPlaceholder = "{agent_id}";
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/participants/{agent_id}";
    }

    // Sending a notification about a state content change
    public static class SendAgentConversationInsightsEvent
    {
        public const string AgentPlaceholder = "{agent_id}";
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/assistants/{agent_id}/states/events?conversation_id={conversation_id}";
    }

    // Get list of files
    public static class GetConversationFiles
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/files";
    }

    // Download/Delete file
    public static class ConversationFile
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string FileNamePlaceholder = "{filename}";
        public const string Path = "/conversations/{conversation_id}/files/{filename}";
    }

    // Upload file
    public static class UploadConversationFile
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/files";
    }
}
