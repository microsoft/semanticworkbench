// Copyright (c) Microsoft. All rights reserved.
import { CopilotChat, ResponseCount } from '@fluentui-copilot/react-copilot';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { useLocation } from 'react-router-dom';
import AutoSizer from 'react-virtualized-auto-sizer';
import { Virtuoso, VirtuosoHandle } from 'react-virtuoso';
import { Constants } from '../../Constants';
import { WorkbenchEventSource } from '../../libs/WorkbenchEventSource';
import { useEnvironment } from '../../libs/useEnvironment';
import { Conversation } from '../../models/Conversation';
import { conversationMessageFromJSON } from '../../models/ConversationMessage';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch } from '../../redux/app/hooks';
import {
    conversationApi,
    updateGetConversationParticipantsQueryData,
    useGetConversationMessagesQuery,
} from '../../services/workbench';
import { Loading } from '../App/Loading';
import { InteractMessage } from './InteractMessage';
import { ParticipantStatus } from './ParticipantStatus';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
    root: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
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
}

export const InteractHistory: React.FC<InteractHistoryProps> = (props) => {
    const { conversation, participants, readOnly } = props;
    const classes = useClasses();
    const { hash } = useLocation();
    const [items, setItems] = React.useState<React.ReactNode[]>([]);
    const [hashItemIndex, setHashItemIndex] = React.useState<number>();
    const environment = useEnvironment();
    const dispatch = useAppDispatch();

    const {
        data: messages,
        error: getMessagesError,
        isLoading: isLoadingMessages,
    } = useGetConversationMessagesQuery(conversation.id);

    if (getMessagesError) {
        const errorMessage = JSON.stringify(getMessagesError);
        throw new Error(`Error loading messages: ${errorMessage}`);
    }

    const virtuosoRef = React.useRef<VirtuosoHandle>(null);
    const [shouldAutoScroll, setShouldAutoScroll] = React.useState<boolean>(true);

    // create a function to scroll to the bottom of the chat
    // to be used whenever we need to force a scroll to the bottom
    const performScrollToBottom = React.useCallback(() => {
        if (shouldAutoScroll) {
            // wait a tick for the DOM to update
            setTimeout(() => {
                virtuosoRef.current?.scrollToIndex({ index: items.length - 1 });
            }, 0);
        }
    }, [items.length, shouldAutoScroll]);

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

    // scroll to the bottom when the participant status changes
    const handleParticipantStatusChange = React.useCallback(() => {
        performScrollToBottom();
    }, [performScrollToBottom]);

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
                const date = dayjs.utc(message.timestamp).tz(dayjs.tz.guess()).format('M/D/YY');
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
                        <InteractMessage
                            readOnly={readOnly}
                            conversationId={conversation.id}
                            message={message}
                            participant={senderParticipant}
                            hideParticipant={hideParticipant}
                            displayDate={displayDate}
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
        conversation.id,
        handleParticipantStatusChange,
        hash,
        hashItemIndex,
        isLoadingMessages,
        messages,
        participants,
        readOnly,
    ]);

    React.useEffect(() => {
        if (isLoadingMessages || !messages) {
            return;
        }

        // handle new message events
        const messageHandler = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            const parsedEventData = {
                timestamp: data.timestamp,
                data: {
                    message: conversationMessageFromJSON(data.message),
                },
            };

            if (parsedEventData.data.message.messageType === 'log') {
                // ignore log messages
                return;
            }

            dispatch(
                conversationApi.endpoints.getConversationMessages.initiate(conversation.id, {
                    forceRefetch: true,
                }),
            );
        };

        // handle participant events
        const handleParticipantEvent = (event: {
            timestamp: string;
            data: {
                participant: ConversationParticipant;
                participants: ConversationParticipant[];
            };
        }) => {
            // update the conversation participants in the cache
            dispatch(updateGetConversationParticipantsQueryData(conversation.id, event.data));
        };

        const participantCreatedHandler = (event: EventSourceMessage) => {
            handleParticipantEvent(JSON.parse(event.data));
        };

        const participantUpdatedHandler = (event: EventSourceMessage) => {
            handleParticipantEvent(JSON.parse(event.data));
        };

        (async () => {
            // create or update the event source
            const workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversation.id);
            workbenchEventSource.addEventListener('message.created', messageHandler);
            workbenchEventSource.addEventListener('message.deleted', messageHandler);
            workbenchEventSource.addEventListener('participant.created', participantCreatedHandler);
            workbenchEventSource.addEventListener('participant.updated', participantUpdatedHandler);
        })();

        return () => {
            (async () => {
                const workbenchEventSource = await WorkbenchEventSource.getInstance();
                workbenchEventSource.removeEventListener('message.created', messageHandler);
                workbenchEventSource.removeEventListener('message.deleted', messageHandler);
                workbenchEventSource.removeEventListener('participant.created', participantCreatedHandler);
                workbenchEventSource.removeEventListener('participant.updated', participantUpdatedHandler);
            })();
        };
    }, [conversation.id, dispatch, environment.url, isLoadingMessages, messages]);

    if (isLoadingMessages || !messages) {
        return <Loading />;
    }

    return (
        <CopilotChat style={{ height: '100%' }}>
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
                        atBottomStateChange={(isAtBottom) => {
                            if (isAtBottom) {
                                setShouldAutoScroll(true);
                            } else {
                                setShouldAutoScroll(false);
                            }
                        }}
                    />
                )}
            </AutoSizer>
        </CopilotChat>
    );
};
