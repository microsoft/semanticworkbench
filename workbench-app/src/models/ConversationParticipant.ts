// Copyright (c) Microsoft. All rights reserved.

export interface ConversationParticipant {
    role: 'user' | 'assistant' | 'service';
    id: string;
    conversationId: string;
    name: string;
    image?: string;
    online?: boolean;
    status: string | null;
    statusTimestamp: string | null;
    conversationPermission: 'read' | 'read_write';
    active: boolean;
    metadata: {
        [key: string]: any;
    };
}
