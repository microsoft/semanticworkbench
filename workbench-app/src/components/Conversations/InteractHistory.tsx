// Copyright (c) Microsoft. All rights reserved.
import { CopilotChat, ResponseCount } from '@fluentui-copilot/react-copilot';
import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { useLocation } from 'react-router-dom';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import { Constants } from '../../Constants';
import { Utility } from '../../libs/Utility';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useUpdateConversationParticipantMutation } from '../../services/workbench';
import { MemoizedInteractMessage } from './Message/InteractMessage';
import { MemoizedNotificationAccordion } from './Message/NotificationAccordion';
import { MemoizedToolResultMessage } from './Message/ToolResultMessage';
import { ParticipantStatus } from './ParticipantStatus';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
    root: {
        height: '100%',
    },
    loading: {
        ...shorthands.margin(tokens.spacingVerticalXXXL, 0),
    },
    virtuoso: {
        '::-webkit-scrollbar-thumb': {
            backgroundColor: tokens.colorNeutralStencil1Alpha,
        },
    },
    item: {
        lineHeight: tokens.lineHeightBase400,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    counter: {
        ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXXXL, 0),
    },
    status: {
        ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalXXXL, 0),
    },
});

interface InteractHistoryProps {
    conversation: Conversation;
    messages: ConversationMessage[];
    participants: ConversationParticipant[];
    readOnly: boolean;
    className?: string;
    onRewindToBefore?: (message: ConversationMessage, redo: boolean) => Promise<void>;
}

export const InteractHistory: React.FC<InteractHistoryProps> = (props) => {
    const { conversation, messages, participants, readOnly, className, onRewindToBefore } = props;
    const classes = useClasses();
    const { hash } = useLocation();
    const { debouncedSetLastRead } = useConversationUtility();
    const [scrollToIndex, setScrollToIndex] = React.useState<number>();
    const [items, setItems] = React.useState<React.ReactNode[]>([]);
    const [isAtBottom, setIsAtBottom] = React.useState<boolean>(true);
    const [updateParticipantState] = useUpdateConversationParticipantMutation();

    // handler for when a message is read
    const handleOnRead = React.useCallback(
        // update the last read timestamp for the conversation
        async (message: ConversationMessage) => debouncedSetLastRead(conversation, message.timestamp),
        [debouncedSetLastRead, conversation],
    );

    const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const debouncedUpdateViewingMessage = React.useCallback(
        (conversationId: string, messageTimestamp: string) => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(
                () =>
                    updateParticipantState({
                        conversationId,
                        participantId: 'me',
                        metadata: {
                            viewing_message_timestamp: messageTimestamp,
                        },
                    })?.unwrap(),
                300,
            );
        },
        [updateParticipantState],
    );

    // handler for when a message is visible
    const handleOnVisible = React.useCallback(
        async (message: ConversationMessage) => {
            debouncedUpdateViewingMessage(conversation.id, message.timestamp);
        },
        [conversation.id, debouncedUpdateViewingMessage],
    );

    // create a ref for the virtuoso component for using its methods directly
    const virtuosoRef = React.useRef<VirtuosoHandle>(null);

    // set the scrollToIndex to the last item if the user is at the bottom of the history
    const triggerAutoScroll = React.useCallback(() => {
        if (isAtBottom) {
            setScrollToIndex(items.length - 1);
        }
    }, [isAtBottom, items.length]);

    // trigger auto scroll when the items change
    React.useEffect(() => {
        triggerAutoScroll();
    }, [items, triggerAutoScroll]);

    // scroll to the bottom of the history when the scrollToIndex changes
    React.useEffect(() => {
        if (!scrollToIndex) {
            return;
        }

        const index = scrollToIndex;
        setScrollToIndex(undefined);

        // wait a tick for the DOM to update
        setTimeout(() => virtuosoRef.current?.scrollToIndex({ index, align: 'start' }), 0);
    }, [scrollToIndex]);

    // create a list of memoized interact message components for rendering in the virtuoso component
    React.useEffect(() => {
        let lastDate = '';
        let generatedResponseCount = 0;

        // Filter out log messages first
        const filteredMessages = messages.filter((message) => message.messageType !== 'log');

        // Group sequential notification messages
        const groupedItems: React.ReactNode[] = [];
        let currentNotificationGroup: ConversationMessage[] = [];
        let lastNotificationTime: dayjs.Dayjs | undefined;

        const finishCurrentGroup = (insertIndex?: number) => {
            if (currentNotificationGroup.length > 0) {
                if (currentNotificationGroup.length === 1) {
                    // Single notification - render normally
                    const message = currentNotificationGroup[0];
                    const item = renderSingleMessage(message, insertIndex);
                    if (item) groupedItems.push(item);
                } else {
                    // Multiple notifications - render as accordion
                    const accordionItem = (
                        <div className={classes.item} key={`accordion-${currentNotificationGroup[0].id}`}>
                            <MemoizedNotificationAccordion
                                messages={currentNotificationGroup}
                                participants={participants}
                                conversation={conversation}
                                readOnly={readOnly}
                                onRead={handleOnRead}
                                onVisible={handleOnVisible}
                                onRewindToBefore={onRewindToBefore}
                            />
                        </div>
                    );
                    groupedItems.push(accordionItem);
                }
                currentNotificationGroup = [];
            }
        };

        const renderSingleMessage = (message: ConversationMessage, originalIndex?: number) => {
            // if a hash is provided, check if the message id matches the hash
            if (hash === `#${message.id}`) {
                // set the hash item index to scroll to the item
                setScrollToIndex(originalIndex ?? groupedItems.length);
            }

            const senderParticipant = participants.find(
                (participant) => participant.id === message.sender.participantId,
            );
            if (!senderParticipant) {
                // if the sender participant is not found, do not render the message.
                // this can happen temporarily if the provided conversation was just
                // re-retrieved, but the participants have not been re-retrieved yet
                return (
                    <div key={message.id} className={classes.item}>
                        Participant not found: {message.sender.participantId} in conversation {conversation.id}
                    </div>
                );
            }

            const date = Utility.toFormattedDateString(message.timestamp, 'M/D/YY');
            let displayDate = false;
            if (date !== lastDate) {
                displayDate = true;
                lastDate = date;
            }

            if (
                message.messageType === 'chat' &&
                message.sender.participantRole !== 'user' &&
                message.metadata?.generated_content !== false
            ) {
                generatedResponseCount += 1;
            }

            // FIXME: add new message type in workbench service/app for tool results
            const isToolResult = message.messageType === 'note' && message.metadata?.['tool_result'];

            // Use memoized message components to prevent re-rendering all messages when one changes
            const messageContent = isToolResult ? (
                <MemoizedToolResultMessage conversation={conversation} message={message} readOnly={readOnly} />
            ) : (
                <MemoizedInteractMessage
                    readOnly={readOnly}
                    conversation={conversation}
                    message={message}
                    participant={senderParticipant}
                    hideParticipant={false} // Single messages show participant
                    displayDate={displayDate}
                    onRead={handleOnRead}
                    onVisible={handleOnVisible}
                    onRewind={onRewindToBefore}
                />
            );

            return (
                <div className={classes.item} key={message.id}>
                    {messageContent}
                </div>
            );
        };

        filteredMessages.forEach((message, index) => {
            const senderParticipant = participants.find(
                (participant) => participant.id === message.sender.participantId,
            );

            // Skip if participant not found
            if (!senderParticipant) {
                finishCurrentGroup(index);
                const errorItem = renderSingleMessage(message, index);
                if (errorItem) groupedItems.push(errorItem);
                return;
            }

            const isNotification = message.messageType !== 'chat';
            const messageTime = dayjs.utc(message.timestamp);

            if (isNotification) {
                // Check if this notification should be grouped with the previous ones
                // Group all sequential notifications within 1 minute regardless of sender
                const shouldGroup = currentNotificationGroup.length > 0 &&
                    lastNotificationTime &&
                    messageTime.diff(lastNotificationTime, 'minute') < 1;

                if (shouldGroup) {
                    // Add to current group
                    currentNotificationGroup.push(message);
                } else {
                    // Finish current group and start new one
                    finishCurrentGroup(index);
                    currentNotificationGroup = [message];
                }

                lastNotificationTime = messageTime;
            } else {
                // Chat message - finish any current notification group
                finishCurrentGroup(index);
                
                // Render chat message normally
                const item = renderSingleMessage(message, index);
                if (item) groupedItems.push(item);
            }
        });

        // Finish any remaining notification group
        finishCurrentGroup();

        const updatedItems = groupedItems;

        if (generatedResponseCount > 0) {
            updatedItems.push(
                <div className={classes.counter} key="response-count">
                    <ResponseCount status="success">
                        {generatedResponseCount} generated response{generatedResponseCount === 1 ? '' : 's'}
                    </ResponseCount>
                </div>,
            );
        }

        updatedItems.push(
            <div className={classes.status} key="participant-status">
                <ParticipantStatus participants={participants} onChange={() => triggerAutoScroll()} />
            </div>,
        );

        setItems(updatedItems);
    }, [
        messages,
        classes.status,
        classes.item,
        classes.counter,
        participants,
        hash,
        readOnly,
        conversation,
        handleOnRead,
        onRewindToBefore,
        isAtBottom,
        items.length,
        triggerAutoScroll,
        handleOnVisible,
    ]);

    // render the history
    return (
        <CopilotChat className={mergeClasses(classes.root, className)}>
            <AutoSizer>
                {({ height, width }: { height: number; width: number }) => (
                    <Virtuoso
                        ref={virtuosoRef}
                        style={{ height, width }}
                        className={classes.virtuoso}
                        data={items}
                        itemContent={(_index, item) => item}
                        initialTopMostItemIndex={items.length}
                        atBottomThreshold={Constants.app.autoScrollThreshold}
                        atBottomStateChange={(isAtBottom) => setIsAtBottom(isAtBottom)}
                    />
                )}
            </AutoSizer>
        </CopilotChat>
    );
};
