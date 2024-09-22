// Copyright (c) Microsoft. All rights reserved.

import { User } from './User';

export interface ConversationShare {
    id: string;
    createdByUser: User;
    label: string;
    conversationId: string;
    conversationTitle: string;
    conversationPermission: 'read' | 'read_write';
    isRedeemable: boolean;
    createdDateTime: string;
    metadata: {
        [key: string]: any;
    };
}
