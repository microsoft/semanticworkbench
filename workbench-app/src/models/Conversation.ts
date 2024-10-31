// Copyright (c) Microsoft. All rights reserved.

import { ConversationMessage } from './ConversationMessage';
import { ConversationParticipant } from './ConversationParticipant';

export interface Conversation {
    id: string;
    ownerId: string;
    title: string;
    created: string;
    latest_message?: ConversationMessage;
    participants: ConversationParticipant[];
    metadata?: {
        [key: string]: any;
    };
    conversationPermission: 'read' | 'read_write';
    importedFromConversationId?: string;
}
