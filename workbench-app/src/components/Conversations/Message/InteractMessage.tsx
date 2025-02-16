// Copyright (c) Microsoft. All rights reserved.

import { MessageBase } from './MessageBase';

import { CopilotMessageV2, Timestamp, UserMessageV2 } from '@fluentui-copilot/react-copilot';
import { Divider, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

import { ParticipantAvatar } from '../ParticipantAvatar';
import { ToolCalls } from '../ToolCalls';
import { MessageActions } from './MessageActions';
import { MessageBody } from './MessageBody';
import { MessageFooter } from './MessageFooter';
import { MessageHeader } from './MessageHeader';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        boxSizing: 'border-box',
        paddingTop: tokens.spacingVerticalXXXL,

        '&.no-header': {
            paddingTop: 0,
        },
    },
    alignForUser: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
    },
    hideParticipant: {
        paddingLeft: tokens.spacingHorizontalXXL,

        '> .fai-CopilotMessage__avatar': {
            display: 'none',
        },

        '> .fai-CopilotMessage__name': {
            display: 'none',
        },

        '> .fai-CopilotMessage__disclaimer': {
            display: 'none',
        },
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        ...shorthands.margin(tokens.spacingVerticalM, 0, tokens.spacingVerticalXS, 0),
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalS),
        gap: tokens.spacingHorizontalS,
    },
    note: {
        boxSizing: 'border-box',
        paddingLeft: tokens.spacingHorizontalXXXL,
    },
    user: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        alignItems: 'flex-end',
    },
    userContent: {
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalXXXL),
    },
    assistantContent: {
        gridTemplateColumns: 'max-content max-content 1fr',
        rowGap: 0,
        maxWidth: 'unset',

        '> .fai-CopilotMessage__content': {
            width: '100%',
            ...shorthands.margin(tokens.spacingVerticalM, 0),
        },
    },
});

interface InteractMessageProps {
    conversation: Conversation;
    message: ConversationMessage;
    participant: ConversationParticipant;
    hideParticipant?: boolean;
    displayDate?: boolean;
    readOnly: boolean;
    onRead?: (message: ConversationMessage) => void;
    onRewind?: (message: ConversationMessage, redo: boolean) => void;
}

export const InteractMessage: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant, hideParticipant, displayDate, readOnly, onRead, onRewind } = props;
    const classes = useClasses();
    const { isMessageVisible, isUnread } = useConversationUtility();

    const isUser = participant.role === 'user';
    const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');

    React.useEffect(() => {
        // Check if the message is visible and unread. If so, trigger the onRead handler to mark it read.
        // If the message is visible, mark it as read by invoking the onRead handler.
        if (isMessageVisible && isUnread(conversation, message.timestamp)) {
            onRead?.(message);
        }
    }, [isMessageVisible, isUnread, message.timestamp, onRead, conversation, message]);

    const header = hideParticipant ? null : (
        <MessageHeader
            message={message}
            participant={participant}
            className={mergeClasses(classes.header, isUser ? classes.alignForUser : undefined)}
        />
    );

    const actions = (
        <MessageActions
            readOnly={readOnly}
            message={message}
            conversation={conversation}
            onRewind={isUser ? onRewind : undefined}
        />
    );

    const body = <MessageBody message={message} conversation={conversation} />;

    const footer = <MessageFooter message={message} />;

    const composedMessage =
        participant.role === 'assistant' ? (
            <CopilotMessageV2
                className={mergeClasses(
                    classes.assistantContent,
                    hideParticipant ? classes.hideParticipant : undefined,
                )}
                avatar={<ParticipantAvatar hideName participant={participant} />}
                name={participant.name}
                actions={actions}
                footnote={footer}
            >
                {body}
                <ToolCalls message={message} />
            </CopilotMessageV2>
        ) : !hideParticipant ? (
            <div className={classes.user}>
                {header}
                <UserMessageV2 className={classes.userContent}>{body}</UserMessageV2>
                {actions}
                {footer}
            </div>
        ) : (
            <MessageBase className={classes.note} header={header} body={body} footer={footer} />
        );

    return (
        <div className={mergeClasses(classes.root, hideParticipant ? 'no-header' : undefined)}>
            {displayDate && (
                <Divider>
                    <Timestamp>{date}</Timestamp>
                </Divider>
            )}
            {composedMessage}
        </div>
    );
};

export const MemoizedInteractMessage = React.memo(InteractMessage);
