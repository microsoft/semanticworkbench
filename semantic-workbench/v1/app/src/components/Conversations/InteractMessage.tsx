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
    Document16Regular,
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
import { RewindConversation } from './RewindConversation';

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
    renderedContent: {
        display: 'flex',
        flexDirection: 'column',
        width: 'fit-content',
        gap: tokens.spacingVerticalM,
    },
    userContent: {
        alignItems: 'end',
    },
    attachment: {
        display: 'flex',
        width: 'fit-content',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
        backgroundColor: tokens.colorNeutralBackground3,
        borderRadius: tokens.borderRadiusMedium,
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

    let rootClassName = classes.root;
    let contentClassName = classes.renderedContent;
    if (hideParticipant) {
        rootClassName = mergeClasses(classes.root, classes.hideParticipantRoot);
    }
    if (isUser) {
        rootClassName = mergeClasses(rootClassName, classes.userRoot);
        contentClassName = mergeClasses(contentClassName, classes.userContent);
    }

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
        let renderedContent: JSX.Element;
        if (message.messageType === 'notice') {
            renderedContent = (
                <div className={classes.noticeContent}>
                    <SystemMessage className={classes.innerContent} icon={<AlertUrgent24Regular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        } else if (message.messageType === 'note') {
            renderedContent = (
                <div className={classes.noteContent}>
                    <SystemMessage className={classes.innerContent} icon={<Note24Regular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        } else if (message.messageType === 'command') {
            renderedContent = (
                <div className={classes.noteContent}>
                    <SystemMessage className={classes.innerContent} icon={<KeyCommandRegular />} message={content}>
                        {content}
                    </SystemMessage>
                </div>
            );
        } else if (message.messageType === 'command-response') {
            renderedContent = (
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
        } else if (isUser) {
            renderedContent = <UserMessage>{content}</UserMessage>;
        } else {
            renderedContent = <CopilotMessage>{content}</CopilotMessage>;
        }

        const attachments = message.filenames?.map((filename) => (
            <div key={filename} className={classes.attachment}>
                <Document16Regular />
                {filename}
            </div>
        ));

        return (
            <div className={contentClassName}>
                {renderedContent}
                {attachments}
            </div>
        );
    }, [
        classes.attachment,
        classes.innerContent,
        classes.noteContent,
        classes.noticeContent,
        content,
        contentClassName,
        isUser,
        message.filenames,
        message.messageType,
    ]);

    const renderedContent = getRenderedMessage();
    const actions = (
        <div>
            <DebugInspector debug={message.metadata?.debug} />
            <MessageDelete conversationId={conversationId} message={message} />
            <RewindConversation conversationId={conversationId} message={message} />
        </div>
    );

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
