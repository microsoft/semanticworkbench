// Copyright (c) Microsoft. All rights reserved.

import { CopilotMessage, SystemMessage, Timestamp, UserMessage } from '@fluentui-copilot/react-copilot';
import {
    Divider,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Text,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    AlertUrgent24Regular,
    AppGenericRegular,
    BotRegular,
    KeyCommandRegular,
    Note24Regular,
    PersonRegular,
    TextBulletListSquareSparkleRegular,
} from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useCreateConversationMessageMutation } from '../../services/workbench';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';
import { DebugInspector } from './DebugInspector';
import { MessageDelete } from './MessageDelete';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        boxSizing: 'border-box',
        ...shorthands.padding(tokens.spacingVerticalL, 0, 0, 0),
    },
    hideParticipantRoot: {
        paddingTop: 0,
    },
    userRoot: {
        alignItems: 'end',
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
});

interface InteractMessageProps {
    conversationId: string;
    message: ConversationMessage;
    participant: ConversationParticipant;
    hideParticipant?: boolean;
    displayDate?: boolean;
}

export const InteractMessage: React.FC<InteractMessageProps> = (props) => {
    const { conversationId, message, participant, hideParticipant, displayDate } = props;
    const classes = useClasses();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const isUser = participant.role === 'user';

    const date = dayjs.utc(message.timestamp).tz(dayjs.tz.guess()).format('dddd, MMMM D');
    const time = dayjs.utc(message.timestamp).tz(dayjs.tz.guess()).format('h:mm A');

    const attribution = React.useMemo(() => {
        if (message.metadata?.attribution) {
            return <Text size={300}>[{message.metadata.attribution}]</Text>;
        }
        return null;
    }, [message.metadata?.attribution]);

    const content = React.useMemo(() => {
        const onSubmit = async (data: string) => {
            if (message.metadata?.command) {
                await createConversationMessage({
                    conversationId,
                    content: JSON.stringify({
                        command: message.metadata.command,
                        parameters: data,
                    }),
                    messageType: 'command',
                });
            }
        };

        return (
            <ContentRenderer
                content={message.content}
                contentType={message.contentType}
                metadata={message.metadata}
                onSubmit={onSubmit}
            />
        );
    }, [conversationId, createConversationMessage, message.content, message.contentType, message.metadata]);

    const getRenderedMessage = React.useCallback(() => {
        if (message.messageType === 'notice') {
            return (
                <div className={classes.noticeContent}>
                    <SystemMessage className={classes.innerContent} icon={<AlertUrgent24Regular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        }

        if (message.messageType === 'note') {
            return (
                <div className={classes.noteContent}>
                    <SystemMessage className={classes.innerContent} icon={<Note24Regular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        }

        if (message.messageType === 'command') {
            return (
                <div className={classes.noteContent}>
                    <SystemMessage className={classes.innerContent} icon={<KeyCommandRegular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        }

        if (message.messageType === 'command-response') {
            return (
                <div className={classes.noteContent}>
                    <SystemMessage
                        className={classes.innerContent}
                        icon={<TextBulletListSquareSparkleRegular />}
                        message={content}
                    >
                        {content}
                    </SystemMessage>
                </div>
            );
        }

        if (isUser) {
            return <UserMessage>{content}</UserMessage>;
        }

        return <CopilotMessage>{content}</CopilotMessage>;
    }, [classes, content, isUser, message.messageType]);

    const renderedContent = getRenderedMessage();
    const actions = (
        <div>
            <DebugInspector debug={message.metadata?.debug} />
            <MessageDelete conversationId={conversationId} message={message} />
        </div>
    );

    let rootClassName = classes.root;
    if (hideParticipant) {
        rootClassName = mergeClasses(classes.root, classes.hideParticipantRoot);
    }
    if (isUser) {
        rootClassName = mergeClasses(rootClassName, classes.userRoot);
    }

    return (
        <div className={rootClassName}>
            {displayDate && (
                <Divider>
                    <Timestamp>{date}</Timestamp>
                </Divider>
            )}
            {hideParticipant ? (
                <Popover openOnHover withArrow positioning="before">
                    <PopoverTrigger>{renderedContent}</PopoverTrigger>
                    <PopoverSurface>{actions}</PopoverSurface>
                </Popover>
            ) : (
                <>
                    <div className={classes.header}>
                        <Persona
                            size="extra-small"
                            name={participant.name}
                            avatar={{
                                name: '',
                                icon: {
                                    user: <PersonRegular />,
                                    assistant: <BotRegular />,
                                    service: <AppGenericRegular />,
                                }[participant.role],
                            }}
                        />
                        {attribution}
                        <div>
                            <Timestamp>{time}</Timestamp>
                        </div>
                        {actions}
                    </div>
                    {renderedContent}
                </>
            )}
        </div>
    );
};
