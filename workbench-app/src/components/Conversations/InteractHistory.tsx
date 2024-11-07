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
import { useEnvironment } from '../../libs/useEnvironment';
import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch } from '../../redux/app/hooks';
import {
    conversationApi,
    updateGetConversationParticipantsQueryData,
    useGetConversationMessagesQuery,
} from '../../services/workbench';
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
    const [items, setItems] = React.useState<React.ReactNode[]>([]);
    const [mayHaveEarlierMessages, setMayHaveEarlierMessages] = React.useState<boolean>(true);
    const [isAtTop, setIsAtTop] = React.useState<boolean>(false);
    const [isAtBottom, setIsAtBottom] = React.useState<boolean>(true);
    const [before, setBefore] = React.useState<string>();
    const [after, setAfter] = React.useState<string>();
    const [hashItemIndex, setHashItemIndex] = React.useState<number>();
    const { setLastRead } = useConversationUtility();
    const environment = useEnvironment();
    const dispatch = useAppDispatch();

    const {
        data: messages,
        error: getMessagesError,
        isLoading: isLoadingMessages,
    } = useGetConversationMessagesQuery({ conversationId: conversation.id });

    const onMessageCreated = React.useCallback(() => {
        dispatch(
            conversationApi.endpoints.getConversationMessages.initiate(
                { conversationId: conversation.id },
                {
                    forceRefetch: true,
                },
            ),
        );
    }, [dispatch, conversation.id]);

    const onMessageDeleted = React.useCallback(
        (messageId: string) => {
            dispatch(
                conversationApi.endpoints.getConversationMessages.initiate(
                    { conversationId: conversation.id },
                    {
                        forceRefetch: true,
                    },
                ),
            );
        },
        [dispatch, conversation.id],
    );

    const onParticipantCreated = React.useCallback(
        (participant: ConversationParticipant) => {
            dispatch(updateGetConversationParticipantsQueryData(conversation.id, { participant, participants }));
        },
        [dispatch, conversation.id, participants],
    );

    const onParticipantUpdated = React.useCallback(
        (participant: ConversationParticipant) => {
            dispatch(updateGetConversationParticipantsQueryData(conversation.id, { participant, participants }));
        },
        [dispatch, conversation.id, participants],
    );

    useConversationEvents(conversation.id, {
        onMessageCreated,
        onMessageDeleted,
        onParticipantCreated,
        onParticipantUpdated,
    });

    if (getMessagesError) {
        const errorMessage = JSON.stringify(getMessagesError);
        throw new Error(`Error loading messages: ${errorMessage}`);
    }

    const virtuosoRef = React.useRef<VirtuosoHandle>(null);

    // React.useEffect(() => {
    //     if (isAtTop && mayHaveEarlierMessages && !isLoadingMessages) {
    //         const new_messages = await dispatch(
    //             conversationApi.endpoints.getConversationMessages.initiate(
    //                 { conversationId: conversation.id, before },
    //                 {
    //                     forceRefetch: true,
    //                 },
    //             ),
    //         ).unwrap();
    //     }
    // }, [isAtTop, mayHaveEarlierMessages, isLoadingMessages, handleLoadMore, dispatch, conversation.id, before]);

    // create a function to scroll to the bottom of the chat
    // to be used whenever we need to force a scroll to the bottom
    const performScrollToBottom = React.useCallback(() => {
        if (isAtBottom) {
            // wait a tick for the DOM to update
            setTimeout(() => {
                virtuosoRef.current?.scrollToIndex({ index: items.length - 1 });
            }, 0);
        }
    }, [items.length, isAtBottom]);

    // const performScrollToTop = React.useCallback(() => {
    //     if (isAtTop) {
    //         // wait a tick for the DOM to update
    //         setTimeout(() => {
    //             virtuosoRef.current?.scrollToIndex({ index: 0 });
    //         }, 0);
    //     }
    // }, [isAtTop]);

    // scroll to the bottom when the component mounts
    // and whenever the items change, such as when new messages are added
    React.useEffect(() => {
        performScrollToBottom();
    }, [performScrollToBottom]);

    // if hash index is set, scroll to the hash item
    React.useEffect(() => {
        if (hashItemIndex !== undefined) {
            setTimeout(() => {
                virtuosoRef.current?.scrollToIndex({ index: hashItemIndex });
            }, 0);
        }
    }, [hashItemIndex]);

    // // handle loading more messages when scrolling to the top or bottom
    // const handleLoadMore = React.useCallback(
    //     (direction: 'top' | 'bottom') => {
    //         if (isLoadingMessages || !messages) {
    //             return;
    //         }
    //         if (direction === 'top' && messages.length > 0) {
    //             setBefore(messages[0].id);
    //         } else if (direction === 'bottom' && messages.length > 0) {
    //             setAfter(messages[messages.length - 1].id);
    //         }
    //     },
    //     [isLoadingMessages, messages],
    // );

    // // attach scroll event listener to load more messages
    // React.useEffect(() => {
    //     const virtuoso = virtuosoRef.current;
    //     if (virtuoso) {
    //         virtuoso.scrollToIndex({
    //             // index: 0,
    //             index: items.length - 1,
    //             behavior: 'auto',
    //         });

    //         const handleScroll = () => {
    //             const scrollTop = virtuoso.scrollTop;
    //             const scrollHeight = virtuoso.scrollHeight;
    //             const clientHeight = virtuoso.clientHeight;

    //             if (scrollTop === 0) {
    //                 handleLoadMore('top');
    //             } else if (scrollTop + clientHeight >= scrollHeight) {
    //                 handleLoadMore('bottom');
    //             }
    //         };

    //         virtuoso.addEventListener('scroll', handleScroll);
    //         return () => {
    //             virtuoso.removeEventListener('scroll', handleScroll);
    //         };
    //     }
    // }, [handleLoadMore, items.length]);

    // scroll to the bottom when the participant status changes
    const handleParticipantStatusChange = React.useCallback(() => {
        performScrollToBottom();
    }, [performScrollToBottom]);

    const handleOnRead = React.useCallback(
        (message: ConversationMessage) => {
            setLastRead(conversation, message.timestamp);
        },
        [setLastRead, conversation],
    );

    React.useEffect(() => {
        if (isLoadingMessages || !messages) {
            setItems([]);
            return;
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
                <ParticipantStatus participants={participants} onChange={handleParticipantStatusChange} />
            </div>,
        );
        setItems(updatedItems);
    }, [
        classes.counter,
        classes.item,
        classes.status,
        conversation,
        handleOnRead,
        handleParticipantStatusChange,
        hash,
        hashItemIndex,
        isLoadingMessages,
        messages,
        participants,
        readOnly,
    ]);

    if (isLoadingMessages || !messages) {
        return <Loading />;
    }

    return (
        <CopilotChat className={mergeClasses(classes.root, className ?? '')}>
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
                        atTopStateChange={(isAtTop) => setIsAtTop(isAtTop)}
                        atBottomStateChange={(isAtBottom) => setIsAtBottom(isAtBottom)}
                    />
                )}
            </AutoSizer>
        </CopilotChat>
    );
};
