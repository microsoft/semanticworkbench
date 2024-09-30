// Copyright (c) Microsoft. All rights reserved.

import { User } from './User';

export interface ConversationShareRedemption {
    id: string;
    conversationShareId: string;
    conversationId: string;
    redeemedByUser: User;
    conversationPermission: 'read' | 'read_write';
    createdDateTime: string;
    isNewParticipant: boolean;
}
