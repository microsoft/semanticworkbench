// Copyright (c) Microsoft. All rights reserved.

import { AiGeneratedDisclaimer, Timestamp } from '@fluentui-copilot/react-copilot';
import {
    Divider,
    Popover,
    PopoverSurface,
    PopoverTrigger,
    Text,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Link } from 'react-router-dom';

import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import {
    useCreateConversationMessageMutation,
    useGetConversationMessageDebugDataQuery,
} from '../../../services/workbench';
import { ContentRenderer } from '../ContentRenderers/ContentRenderer';

import { AttachmentSection } from './AttachmentSection';
import { ActionsSection } from './InteractMessage/ActionsSection';
import { ContentSafetyNotice } from './InteractMessage/ContentSafetyNotice';
import { MessageHeader } from './MessageHeader';
import { CopilotMessageRenderer, NoticeMessage, UserMessageRenderer } from './MessageRenderers';

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
    footer: {
        display: 'flex',
        color: tokens.colorNeutralForeground3,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXS, 0, tokens.spacingVerticalXS, tokens.spacingHorizontalS),
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
    onRead?: (message: ConversationMessage) => void;
    onRewind?: (message: ConversationMessage, redo: boolean) => void;
}

export const InteractMessage: React.FC<InteractMessageProps> = (props) => {
    const { conversation, message, participant, hideParticipant, displayDate, readOnly, onRead, onRewind } = props;
    const classes = useClasses();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const { isMessageVisible, isUnread } = useConversationUtility();
    const [skipDebugLoad, setSkipDebugLoad] = React.useState(true);
    const {
        data: debugData,
        isLoading: isLoadingDebugData,
        isUninitialized: isUninitializedDebugData,
    } = useGetConversationMessageDebugDataQuery(
        { conversationId: conversation.id, messageId: message.id },
        { skip: skipDebugLoad },
    );

    const isUser = participant.role === 'user';

    const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');
    const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');

    const attribution = React.useMemo(() => {
        if (message.metadata?.attribution) {
            return <Text size={300}>[{message.metadata.attribution}]</Text>;
        }
        return null;
    }, [message.metadata?.attribution]);

    let rootClassName = classes.root;
    if (hideParticipant) {
        rootClassName = mergeClasses(classes.root, classes.hideParticipantRoot);
    }
    if (isUser) {
        rootClassName = mergeClasses(rootClassName, classes.userRoot, classes.userContent);
    }

    React.useEffect(() => {
        // If the message is visible, mark it as read by invoking the onRead handler.
        if (isMessageVisible && isUnread(conversation, message.timestamp)) {
            onRead?.(message);
        }
    }, [isMessageVisible, isUnread, message.timestamp, onRead, conversation, message]);

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
        return (
            <ContentSafetyNotice
                contentSafety={message.metadata?.['content_safety']}
                noticeClass={classes.notice}
                safetyClass={classes.contentSafetyNotice}
            />
        );
    }, [classes.contentSafetyNotice, classes.notice, message]);

    const actions = React.useMemo(
        () => (
            <ActionsSection
                readOnly={readOnly}
                message={message}
                conversation={conversation}
                debugData={debugData}
                isLoadingDebugData={isLoadingDebugData}
                isUninitializedDebugData={isUninitializedDebugData}
                onRewind={onRewind}
                setSkipDebugLoad={setSkipDebugLoad}
            />
        ),
        [conversation, debugData, isLoadingDebugData, isUninitializedDebugData, message, onRewind, readOnly],
    );

    // Memoize renderedContent for stable dependency management.
    const memoizedRenderedContent = React.useMemo(() => {
        return message.messageType === 'notice' ||
            message.messageType === 'note' ||
            message.messageType === 'command' ||
            message.messageType === 'command-response' ? (
            <NoticeMessage content={content} innerContentClass={classes.innerContent} noteStyle={classes.noteContent} />
        ) : isUser ? (
            <UserMessageRenderer content={content} />
        ) : (
            <CopilotMessageRenderer content={content} />
        );
    }, [message.messageType, content, classes.innerContent, classes.noteContent, isUser]);

    const finalContent = React.useMemo(() => {
        if (message.metadata?.href) {
            return <Link to={message.metadata.href}>{memoizedRenderedContent}</Link>;
        }
        return memoizedRenderedContent;
    }, [message.metadata, memoizedRenderedContent]);

    const attachmentSection = React.useMemo(() => {
        if (message.filenames && message.filenames.length > 0) {
            return (
                <AttachmentSection
                    filenames={message.filenames}
                    message={message}
                    generatedClass={classes.generated}
                    footerItems={message.metadata?.['footer_items']}
                />
            );
        }
        return null;
    }, [message, classes.generated]);

    // Calculate footer content from message metadata footer_items
    const messageFooterContent = React.useMemo(() => {
        if (message.metadata?.['footer_items']) {
            const footerItemsArray = Array.isArray(message.metadata['footer_items'])
                ? message.metadata['footer_items']
                : [message.metadata['footer_items']];
            return (
                <div className={classes.footer}>
                    {footerItemsArray.map((item) => (
                        <AiGeneratedDisclaimer key={item} className={classes.generated}>
                            {item}
                        </AiGeneratedDisclaimer>
                    ))}
                </div>
            );
        }
        return null;
    }, [message.metadata, classes.footer, classes.generated]);

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
                        <div className={classes.renderedContent}>{finalContent}</div>
                    </PopoverTrigger>
                    <PopoverSurface>
                        <div className={classes.popoverContent}>{actions}</div>
                    </PopoverSurface>
                </Popover>
            ) : (
                <>
                    <MessageHeader
                        participant={participant}
                        time={time}
                        attribution={attribution}
                        headerClassName={classes.header}
                    />
                    {/* Placeholder for controls such as actions (links, buttons, etc.) placed directly below the header. */}
                    <div className={classes.footer}>{actions}</div>
                    {finalContent}
                    {contentSafetyNotice}
                    {attachmentSection}
                    {messageFooterContent}
                </>
            )}
        </div>
    );
};

export const MemoizedInteractMessage = React.memo(InteractMessage);
