// Copyright (c) Microsoft. All rights reserved.

export type Assistant = {
    id: string;
    name: string;
    image?: string;
    assistantServiceId: string;
    templateId: string;
    createdDatetime: string;
    conversations: {
        [additionalPropertyId: string]: {
            id: string;
        };
    };
    commands?: {
        [commandName: string]: {
            displayName: string;
            description: string;
        };
    };
    states?: {
        [stateKey: string]: {
            displayName: string;
            description: string;
        };
    };
    metadata?: {
        [key: string]: any;
    };
};
