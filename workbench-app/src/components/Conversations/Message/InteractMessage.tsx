// Copyright (c) Microsoft. All rights reserved.

import { MessageBase } from './MessageBase';

import { Timestamp } from '@fluentui-copilot/react-copilot';
import {
    Divider,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';

import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

import { MessageActions } from './MessageActions';
import { MessageBody } from './MessageBody';
import { MessageFooter } from './MessageFooter';
import { MessageHeader } from './MessageHeader';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        boxSizing: 'border-box',
        ...shorthands.padding(tokens.spacingVerticalL, 0, 0, 0),
    },
    alignForUser: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
    },
    hideParticipantRoot: {
        paddingTop: 0,
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        ...shorthands.margin(tokens.spacingVerticalM, 0, tokens.spacingVerticalXS, 0),
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalS),
        gap: tokens.spacingHorizontalS,
    },
    noteContent: {
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalS),
        ...shorthands.border('none'),
        ...shorthands.margin(0),
    },
    noticeContent: {
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalS),
        ...shorthands.border('none'),
        ...shorthands.margin(0),
    },
    innerContent: {
        maxWidth: '100%',
    },
    renderedContent: {
        display: 'flex',
        flexDirection: 'column',
        width: 'fit-content',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXS, 0, tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
    footer: {
        display: 'flex',
        color: tokens.colorNeutralForeground3,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(0, tokens.spacingHorizontalS),
    },
    userContent: {
        justifyContent: 'flex-end',
        alignItems: 'flex-end',
        display: 'flex',
    },
    generated: {
        width: 'fit-content',
        marginTop: tokens.spacingVerticalS,
    },
    popoverContent: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
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

    let rootClassName = classes.root;
    if (hideParticipant) {
        rootClassName = mergeClasses(classes.root, classes.hideParticipantRoot);
    }
    if (isUser) {
        rootClassName = mergeClasses(rootClassName, classes.alignForUser, classes.userContent);
    }

    React.useEffect(() => {
        // Check if the message is visible and unread. If so, trigger the onRead handler to mark it read.
        // If the message is visible, mark it as read by invoking the onRead handler.
        if (isMessageVisible && isUnread(conversation, message.timestamp)) {
            onRead?.(message);
        }
    }, [isMessageVisible, isUnread, message.timestamp, onRead, conversation, message]);

    const header = (
        <MessageHeader
            message={message}
            participant={participant}
            className={mergeClasses(classes.header, isUser ? classes.alignForUser : undefined)}
        />
    );

    const actions = (
        <MessageActions
            className={isUser ? classes.alignForUser : undefined}
            readOnly={readOnly}
            message={message}
            conversation={conversation}
            onRewind={onRewind}
        />
    );

    const body = <MessageBody message={message} conversation={conversation} participant={participant} />;

    const footer = <MessageFooter message={message} />;

    const composedMessage = <MessageBase header={header} body={body} actions={actions} footer={footer} />;

    return (
        <div className={rootClassName}>
            {displayDate && (
                <Divider>
                    <Timestamp>{date}</Timestamp>
                </Divider>
            )}
            {hideParticipant || (message.messageType === 'notice' && isUser) ? (
                <Popover openOnHover withArrow positioning="before">
                    <PopoverTrigger>
                        <div className={classes.renderedContent}>{composedMessage}</div>
                    </PopoverTrigger>
                    <PopoverSurface>
                        <div className={classes.popoverContent}>{actions}</div>
                    </PopoverSurface>
                </Popover>
            ) : (
                composedMessage
            )}
        </div>
    );
};

export const MemoizedInteractMessage = React.memo(InteractMessage);
