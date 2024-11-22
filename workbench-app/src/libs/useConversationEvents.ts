// Copyright (c) Microsoft. All rights reserved.
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { conversationMessageFromJSON } from '../models/ConversationMessage';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { useAppDispatch } from '../redux/app/hooks';
import { useEnvironment } from './useEnvironment';
import { WorkbenchEventSource, WorkbenchEventSourceType } from './WorkbenchEventSource';

export const useConversationEvents = (
    conversationId: string,
    handlers: {
        onMessageCreated?: () => void;
        onMessageDeleted?: (messageId: string) => void;
        onParticipantCreated?: (participant: ConversationParticipant) => void;
        onParticipantUpdated?: (participant: ConversationParticipant) => void;
    },
) => {
    const { onMessageCreated, onMessageDeleted, onParticipantCreated, onParticipantUpdated } = handlers;
    const environment = useEnvironment();
    const dispatch = useAppDispatch();

    // handle new message events
    const handleMessageEvent = React.useCallback(
        async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            const parsedEventData = {
                timestamp: data.timestamp,
                data: {
                    message: conversationMessageFromJSON(data.message),
                },
            };

            if (event.event === 'message.created') {
                onMessageCreated?.();
            }

            if (event.event === 'message.deleted') {
                onMessageDeleted?.(parsedEventData.data.message.id);
            }
        },
        [onMessageCreated, onMessageDeleted],
    );

    // handle participant events
    const handleParticipantEvent = React.useCallback(
        (event: EventSourceMessage) => {
            const parsedEventData = JSON.parse(event.data) as {
                timestamp: string;
                data: {
                    participant: ConversationParticipant;
                    participants: ConversationParticipant[];
                };
            };

            if (event.event === 'participant.created') {
                onParticipantCreated?.(parsedEventData.data.participant);
            }

            if (event.event === 'participant.updated') {
                onParticipantUpdated?.(parsedEventData.data.participant);
            }
        },
        [onParticipantCreated, onParticipantUpdated],
    );

    React.useEffect(() => {
        (async () => {
            // create or update the event source
            const workbenchEventSource = await WorkbenchEventSource.createOrUpdate(
                environment.url,
                WorkbenchEventSourceType.Conversation,
                conversationId,
            );
            workbenchEventSource.addEventListener('message.created', handleMessageEvent);
            workbenchEventSource.addEventListener('message.deleted', handleMessageEvent);
            workbenchEventSource.addEventListener('participant.created', handleParticipantEvent);
            workbenchEventSource.addEventListener('participant.updated', handleParticipantEvent);
        })();

        return () => {
            (async () => {
                const workbenchEventSource = await WorkbenchEventSource.getInstance(
                    WorkbenchEventSourceType.Conversation,
                );
                workbenchEventSource.removeEventListener('message.created', handleMessageEvent);
                workbenchEventSource.removeEventListener('message.deleted', handleMessageEvent);
                workbenchEventSource.removeEventListener('participant.created', handleParticipantEvent);
                workbenchEventSource.removeEventListener('participant.updated', handleParticipantEvent);
            })();
        };
    }, [conversationId, dispatch, environment.url, handleMessageEvent, handleParticipantEvent]);
};
