// Copyright (c) Microsoft. All rights reserved.

import {
    AiGeneratedDisclaimer,
    Attachment,
    AttachmentList,
    CopilotMessage,
    SystemMessage,
    Timestamp,
    UserMessage,
} from '@fluentui-copilot/react-copilot';
import {
    Divider,
    Persona,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Text,
    Tooltip,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    AlertUrgent24Regular,
    AppGenericRegular,
    Attach24Regular,
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
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useCreateConversationMessageMutation } from '../../services/workbench';
import { CopyButton } from '../App/CopyButton';
import { ContentRenderer } from './ContentRenderers/ContentRenderer';
import { ConversationFileIcon } from './ConversationFileIcon';
import { DebugInspector } from './DebugInspector';
import { MessageDelete } from './MessageDelete';
import { MessageLink } from './MessageLink';
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
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXS, 0, tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
    userContent: {
        alignItems: 'end',
    },
    contentSafetyNotice: {
        color: tokens.colorPaletteRedForeground1,
    },
    generated: {
        width: 'fit-content',
        marginTop: tokens.spacingVerticalS,
    },
    notice: {
        width: 'fit-content',
        fontSize: tokens.fontSizeBase200,
        flexDirection: 'row',
        color: tokens.colorNeutralForeground2,
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    },
    attachments: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        ...shorthands.padding(tokens.spacingVerticalS, 0, 0, 0),
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
}

export const InteractMessage: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant, hideParticipant, displayDate, readOnly } = props;
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
                    conversationId: conversation.id,
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
    }, [conversation, createConversationMessage, message.content, message.contentType, message.metadata]);

    const contentSafetyNotice = React.useMemo(() => {
        const metadata = message.metadata;
        if (!metadata) return null;

        const contentSafety = metadata['content_safety'];
        if (!contentSafety) return null;

        const { result, note } = contentSafety;
        if (!result || result === 'pass') return null;

        const messageNote = `[Content Safety: ${result}] ${
            note || 'this message has been flagged as potentially unsafe'
        }`;

        return <div className={mergeClasses(classes.notice, classes.contentSafetyNotice)}>{messageNote}</div>;
    }, [classes.contentSafetyNotice, classes.notice, message.metadata]);

    const actions = React.useMemo(
        () => (
            <>
                {!readOnly && <MessageLink conversation={conversation} messageId={message.id} />}
                <DebugInspector debug={message.metadata?.debug} />
                <CopyButton data={message.content} tooltip="Copy message" size="small" appearance="transparent" />
                {!readOnly && (
                    <>
                        <MessageDelete conversationId={conversation.id} message={message} />
                        <RewindConversation conversationId={conversation.id} message={message} />
                    </>
                )}
            </>
        ),
        [conversation, message, readOnly],
    );

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

        const attachmentList =
            message.filenames && message.filenames.length > 0 ? (
                <AttachmentList className={classes.attachments}>
                    {message.filenames?.map((filename) => (
                        <Tooltip content={filename} key={filename} relationship="label">
                            <Attachment
                                media={<ConversationFileIcon file={filename} />}
                                content={filename}
                                dismissIcon={<Attach24Regular />}
                            />
                        </Tooltip>
                    ))}
                </AttachmentList>
            ) : null;

        const aiGeneratedDisclaimer =
            isUser || message.metadata?.['generated_content'] === false ? null : (
                <AiGeneratedDisclaimer className={classes.generated}>
                    AI-generated content may be incorrect
                </AiGeneratedDisclaimer>
            );

        return (
            <>
                <div className={classes.actions}>
                    {(message.messageType !== 'notice' || (message.messageType === 'notice' && !isUser)) && actions}
                </div>
                <div className={contentClassName}>{renderedContent}</div>
                {aiGeneratedDisclaimer}
                {attachmentList}
            </>
        );
    }, [
        actions,
        classes.actions,
        classes.attachments,
        classes.generated,
        classes.innerContent,
        classes.noteContent,
        classes.noticeContent,
        content,
        contentClassName,
        isUser,
        message.filenames,
        message.messageType,
        message.metadata,
    ]);

    const renderedContent = getRenderedMessage();

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
                        <div>{renderedContent}</div>
                    </PopoverTrigger>
                    <PopoverSurface>
                        <div className={classes.popoverContent}>{actions}</div>
                    </PopoverSurface>
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
                    </div>
                    {renderedContent}
                    {contentSafetyNotice}
                </>
            )}
        </div>
    );
};
