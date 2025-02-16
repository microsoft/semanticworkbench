// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Link } from 'react-router-dom';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

import { ContentRenderer } from './ContentRenderer';
import { ContentSafetyNotice } from './ContentSafetyNotice';

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    participant: ConversationParticipant;
}

export const MessageBody: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant } = props;

    const body = (
        <>
            <ContentSafetyNotice contentSafety={message.metadata?.['content_safety']} />
            <ContentRenderer conversation={conversation} message={message} participant={participant} />
        </>
    );

    if (message.metadata?.href) {
        return <Link to={message.metadata.href}>{body}</Link>;
    }
    return body;
};
