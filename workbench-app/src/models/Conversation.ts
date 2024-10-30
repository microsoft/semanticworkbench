// Copyright (c) Microsoft. All rights reserved.

import { ConversationMessage } from './ConversationMessage';

export interface Conversation {
    id: string;
    ownerId: string;
    title: string;
    created: string;
    latest_message?: ConversationMessage;
    metadata?: {
        [key: string]: any;
    };
    conversationPermission: 'read' | 'read_write';
    importedFromConversationId?: string;
}
