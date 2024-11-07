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
import { useConversationEvents } from '../../libs/useConversationEvents';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch } from '../../redux/app/hooks';
import { conversationApi, updateGetConversationParticipantsQueryData } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { MemoizedInteractMessage } from './InteractMessage';
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
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    counter: {
        ...shorthands.padding(0, tokens.spacingHorizontalXL),
    },
    status: {
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
});

interface InteractHistoryProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    readOnly: boolean;
    className?: string;
}

export const InteractHistory: React.FC<InteractHistoryProps> = (props) => {
    const { conversation, participants, readOnly, className } = props;
    const classes = useClasses();
    const { hash } = useLocation();
    const [messages, setMessages] = React.useState<ConversationMessage[]>();
    const [isLoadingMessages, setIsLoadingMessages] = React.useState<boolean>(false);
    const [isAtBottom, setIsAtBottom] = React.useState<boolean>(true);
    const [newestMessageId, setNewestMessageId] = React.useState<string>();
    const [hashItemIndex, setHashItemIndex] = React.useState<number>();
    const { setLastRead } = useConversationUtility();
    const dispatch = useAppDispatch();

    // helper for adding messages to the end of the messages state
    const appendMessages = React.useCallback(
        (newMessages: ConversationMessage[]) => {
            // update the messages state with the new messages, placing the new messages at the end
            setMessages((prevMessages) => (prevMessages ? [...prevMessages, ...newMessages] : newMessages));

            // update the newest message id for use with the 'after' parameter in the next request
            setNewestMessageId(newMessages[newMessages.length - 1].id);
        },
        [setMessages],
    );

    // handler for when a new message is created
    const onMessageCreated = React.useCallback(
        async () =>
            // load the latest messages and append them to the messages state
            appendMessages(
                await dispatch(
                    conversationApi.endpoints.getConversationMessages.initiate({
                        conversationId: conversation.id,
                        limit: Constants.app.maxMessagesPerRequest,
                        after: newestMessageId,
                    }),
                ).unwrap(),
            ),
        [appendMessages, dispatch, conversation.id, newestMessageId],
    );

    // handler for when a message is deleted
    const onMessageDeleted = React.useCallback(
        (messageId: string) =>
            // remove the message from the messages state
            setMessages((prevMessages) => {
                if (!prevMessages) {
                    return prevMessages;
                }
                return prevMessages.filter((message) => message.id !== messageId);
            }),
        [],
    );

    // handler for when a new participant is created
    const onParticipantCreated = React.useCallback(
        (participant: ConversationParticipant) =>
            // add the new participant to the cached participants
            dispatch(updateGetConversationParticipantsQueryData(conversation.id, { participant, participants })),
        [dispatch, conversation.id, participants],
    );

    // handler for when a participant is updated
    const onParticipantUpdated = React.useCallback(
        (participant: ConversationParticipant) =>
            // update the participant in the cached participants
            dispatch(updateGetConversationParticipantsQueryData(conversation.id, { participant, participants })),
        [dispatch, conversation.id, participants],
    );

    // subscribe to conversation events
    useConversationEvents(conversation.id, {
        onMessageCreated,
        onMessageDeleted,
        onParticipantCreated,
        onParticipantUpdated,
    });

    // load all messages for the conversation
    const loadMessages = React.useCallback(async () => {
        let mayHaveEarlierMessages = true;
        let allMessages: ConversationMessage[] = [];
        let before: string | undefined;

        // load messages in chunks until we have loaded all the messages
        while (mayHaveEarlierMessages) {
            const response = await dispatch(
                conversationApi.endpoints.getConversationMessages.initiate({
                    conversationId: conversation.id,
                    limit: Constants.app.maxMessagesPerRequest,
                    before,
                }),
            ).unwrap();
            allMessages = [...response, ...allMessages];
            mayHaveEarlierMessages = response.length === Constants.app.maxMessagesPerRequest;
            before = response[0]?.id;
        }

        // set the messages state with all the messages
        setMessages(allMessages);

        // set the newest message id for use with the 'after' parameter in the next request
        setNewestMessageId(allMessages[allMessages.length - 1].id);

        // set loading messages to false
        setIsLoadingMessages(false);
    }, [dispatch, conversation.id]);

    // load initial messages
    React.useEffect(() => {
        if (!messages && !isLoadingMessages) {
            setIsLoadingMessages(true);
            loadMessages();
        }
    }, [messages, loadMessages, isLoadingMessages]);

    // handler for when a message is read
    const handleOnRead = React.useCallback(
        // update the last read timestamp for the conversation
        async (message: ConversationMessage) => await setLastRead(conversation, message.timestamp),
        [setLastRead, conversation],
    );

    // create a ref for the virtuoso component for using its methods directly
    const virtuosoRef = React.useRef<VirtuosoHandle>(null);

    // create a list of memoized interact message components for rendering in the virtuoso component
    const items = React.useMemo(() => {
        if (!messages) {
            return [];
        }

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
                if (hash && hashItemIndex === undefined && hash === `#${message.id}`) {
                    setHashItemIndex(index);
                }

                const senderParticipant = participants.find(
                    (participant) => participant.id === message.sender.participantId,
                );
                if (!senderParticipant) {
                    // throw new Error(
                    //     `Participant not found: ${message.sender.participantId} in conversation ${conversation.id}`,
                    // );

                    // if the sender participant is not found, do not render the message.
                    // this can happen temporarily if the provided conversation was just
                    // re-retrieved, but the participants have not been re-retrieved yet
                    return (
                        <>
                            <div>
                                Participant not found: {message.sender.participantId} in conversation {conversation.id}
                            </div>
                        </>
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
                let hideParticipant = senderParticipant.role === 'service';
                const messageTime = dayjs.utc(message.timestamp);
                // avoid duplicate header for messages from the same participant, if the
                // attribution is the same and the message is within a minute of the last
                if (
                    lastMessageInfo.participantId === senderParticipant.id &&
                    lastMessageInfo.attribution === message.metadata?.attribution &&
                    messageTime.diff(lastMessageInfo.time, 'minute') < 1
                ) {
                    // TODO: not the best user experience as we want to be able to
                    // delete and edit messages and need to show that ux
                    // hideParticipant = true;
                }
                lastMessageInfo = {
                    participantId: senderParticipant.id,
                    attribution: message.metadata?.attribution,
                    time: messageTime,
                };
                return (
                    <div className={classes.item} key={message.id}>
                        {/*
                            Use the memoized interact message component to prevent re-rendering
                            all messages when one message changes
                        */}
                        <MemoizedInteractMessage
                            readOnly={readOnly}
                            conversation={conversation}
                            message={message}
                            participant={senderParticipant}
                            hideParticipant={hideParticipant}
                            displayDate={displayDate}
                            onRead={handleOnRead}
                        />
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
                <ParticipantStatus
                    participants={participants}
                    onChange={() => {
                        if (isAtBottom) {
                            // wait a tick for the DOM to update
                            setTimeout(() => {
                                virtuosoRef.current?.scrollToIndex({ index: items.length - 1, align: 'start' });
                            }, 0);
                        }
                    }}
                />
            </div>,
        );

        return updatedItems;
    }, [
        classes.counter,
        classes.item,
        classes.status,
        conversation,
        handleOnRead,
        hash,
        hashItemIndex,
        isAtBottom,
        messages,
        participants,
        readOnly,
    ]);

    // if hash index is set, scroll to the hash item
    React.useEffect(() => {
        if (hashItemIndex !== undefined) {
            setTimeout(() => {
                virtuosoRef.current?.scrollToIndex({ index: hashItemIndex, align: 'start' });
            }, 0);
        }
    }, [hashItemIndex]);

    // if messages are not loaded, show a loading spinner
    if (isLoadingMessages) {
        return <Loading className={classes.loading} />;
    }

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
