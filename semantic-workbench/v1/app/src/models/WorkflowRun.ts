// Copyright (c) Microsoft. All rights reserved.

export interface WorkflowRun {
    id: string;
    title: string;
    workflowDefinitionId: string;
    currentStateId: string;
    conversationMappings: { conversationId: string; conversationDefinitionId: string }[];
    assistantMappings: { assistantId: string; conversationId: string }[];
    metadata?: Record<string, any>;
}
