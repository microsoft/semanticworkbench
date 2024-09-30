// Copyright (c) Microsoft. All rights reserved.

export interface WorkflowDefinition {
    id: string;
    label: string;
    startStateId: string;
    states: WorkflowState[];
    transitions: WorkflowTransition[];
    definitions: {
        conversations: ConversationDefinition[];
        assistants: AssistantDefinition[];
    };
    instructions: {
        contextTransfer: string;
    };
}

export interface WorkflowState {
    id: string;
    label: string;
    conversationDefinitionId: string;
    forceNewConversationInstance?: boolean;
    assistantDataList: AssistantData[];
    editorData: {
        position: {
            x: number;
            y: number;
        };
    };
    outlets: OutletData[];
}

export interface WorkflowTransition {
    id: string;
    sourceOutletId: string;
    targetStateId: string;
}

export interface ConversationDefinition {
    id: string;
    title: string;
}

export interface AssistantDefinition {
    id: string;
    name: string;
    assistantServiceId: string;
}

export interface AssistantData {
    assistantDefinitionId: string;
    configData: object;
}

export interface OutletData {
    id: string;
    label: string;
    prompts: {
        evaluateTransition: string;
        contextTransfer?: string;
    };
}
