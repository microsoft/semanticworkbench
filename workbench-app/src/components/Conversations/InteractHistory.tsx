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
import { MemoizedInteractMessage } from './Message/InteractMessage';
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

    // handler for when a message is read
    const handleOnRead = React.useCallback(
        // update the last read timestamp for the conversation
        async (message: ConversationMessage) => await debouncedSetLastRead(conversation, message.timestamp),
        [debouncedSetLastRead, conversation],
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
        let lastMessageInfo = {
            participantId: '',
            attribution: undefined as string | undefined,
            time: undefined as dayjs.Dayjs | undefined,
        };
        let lastDate = '';
        let generatedResponseCount = 0;

        const updatedItems = messages
            .filter((message) => message.messageType !== 'log')
            .map((message, index) => {
                // if a hash is provided, check if the message id matches the hash
                if (hash === `#${message.id}`) {
                    // set the hash item index to scroll to the item
                    setScrollToIndex(index);
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

                if (message.messageType === 'chat' && message.sender.participantRole !== 'user') {
                    generatedResponseCount += 1;
                }

                // avoid duplicate header for messages from the same participant, if the
                // attribution is the same and the message is within a minute of the last
                let hideParticipant = message.messageType !== 'chat';
                const messageTime = dayjs.utc(message.timestamp);
                if (
                    lastMessageInfo.participantId === senderParticipant.id &&
                    lastMessageInfo.attribution === message.metadata?.attribution &&
                    messageTime.diff(lastMessageInfo.time, 'minute') < 1
                ) {
                    hideParticipant = true;
                }
                lastMessageInfo = {
                    participantId: senderParticipant.id,
                    attribution: message.metadata?.attribution,
                    time: messageTime,
                };

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
                        hideParticipant={hideParticipant}
                        displayDate={displayDate}
                        onRead={handleOnRead}
                        onRewind={onRewindToBefore}
                    />
                );

                return (
                    <div className={classes.item} key={message.id}>
                        {messageContent}
                    </div>
                );
            });

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
