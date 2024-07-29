// Copyright (c) Microsoft. All rights reserved.

export interface ConversationParticipant {
    role: 'user' | 'assistant' | 'service';
    id: string;
    name: string;
    online?: boolean;
    status: string | null;
    statusTimestamp: string | null;
    active: boolean;
}
