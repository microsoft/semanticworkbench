// Copyright (c) Microsoft. All rights reserved.

export interface NewAssistantServiceRegistration {
    assistantServiceId: string;
    name: string;
    description: string;
    includeInListing: boolean;
}

export interface AssistantServiceRegistration {
    assistantServiceId: string;
    assistantServiceOnline: boolean;
    assistantServiceUrl: string;
    name: string;
    description: string;
    includeInListing: boolean;
    createdDateTime: string;
    createdByUserId: string;
    createdByUserName: string;
    apiKeyName: string;
    apiKey?: string;
}
