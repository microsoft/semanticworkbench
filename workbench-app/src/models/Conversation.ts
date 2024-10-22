// Copyright (c) Microsoft. All rights reserved.

export interface Conversation {
    id: string;
    ownerId: string;
    title: string;
    created: string;
    metadata?: {
        [key: string]: any;
    };
    conversationPermission: 'read' | 'read_write';
    importedFromConversationId?: string;
}
