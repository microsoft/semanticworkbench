// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { Link } from 'react-router-dom';

import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

import { MessageContent } from './MessageContent';
import { CopilotMessageRenderer, NoticeRenderer, UserMessageRenderer } from './MessageRenderers';

const useClasses = makeStyles({
    noteContent: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalS),
        ...shorthands.border('none'),
        ...shorthands.margin(0),
    },
    innerContent: {
        maxWidth: '100%',
    },
});

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    participant: ConversationParticipant;
}

export const MessageBody: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant } = props;
    const classes = useClasses();

    const isUser = participant.role === 'user';

    const messageContent = <MessageContent message={message} conversation={conversation} />;

    const renderedContent =
        message.messageType === 'notice' ||
        message.messageType === 'note' ||
        message.messageType === 'command' ||
        message.messageType === 'command-response' ? (
            <NoticeRenderer
                content={messageContent}
                innerClassName={classes.innerContent}
                className={classes.noteContent}
            />
        ) : isUser ? (
            <UserMessageRenderer content={messageContent} />
        ) : (
            <CopilotMessageRenderer content={messageContent} />
        );

    if (message.metadata?.href) {
        return <Link to={message.metadata.href}>{renderedContent}</Link>;
    }
    return renderedContent;
};
