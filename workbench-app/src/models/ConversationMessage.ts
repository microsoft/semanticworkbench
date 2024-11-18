// Copyright (c) Microsoft. All rights reserved.

export interface ConversationMessage {
    id: string;
    sender: {
        participantId: string;
        participantRole: string;
    };
    timestamp: string;
    content: string;
    messageType: string;
    contentType: string;
    filenames?: string[];
    metadata?: {
        [key: string]: any;
    };
    hasDebugData: boolean;
}

export const conversationMessageFromJSON = (json: any): ConversationMessage => {
    return {
        id: json.id,
        sender: {
            participantId: json.sender.participant_id,
            participantRole: json.sender.participant_role,
        },
        timestamp: json.timestamp,
        content: json.content,
        messageType: json.message_type,
        contentType: json.content_type,
        filenames: json.filenames,
        metadata: json.metadata,
        hasDebugData: json.has_debug_data,
    };
};
