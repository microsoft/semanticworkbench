// Copyright (c) Microsoft. All rights reserved.

export interface Conversation {
    id: string;
    ownerId: string;
    title: string;
    metadata?: {
        [key: string]: any;
    };
}
