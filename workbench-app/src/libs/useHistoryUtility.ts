import React from 'react';
import { Constants } from '../Constants';
import { ConversationMessage } from '../models/ConversationMessage';
import { ConversationParticipant } from '../models/ConversationParticipant';
import { useAppDispatch } from '../redux/app/hooks';
import {
    conversationApi,
    updateGetAllConversationMessagesQueryData,
    updateGetConversationParticipantsQueryData,
    useGetAllConversationMessagesQuery,
    useGetAssistantsInConversationQuery,
    useGetConversationFilesQuery,
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
} from '../services/workbench';
import { useGetAssistantCapabilities } from './useAssistantCapabilities';
import { useConversationEvents } from './useConversationEvents';

export const useHistoryUtility = (conversationId: string) => {
    const dispatch = useAppDispatch();

    const {
        data: conversation,
        error: conversationError,
        isLoading: conversationIsLoading,
    } = useGetConversationQuery(conversationId, { refetchOnMountOrArgChange: true });
    const {
        data: allConversationMessages,
        error: allConversationMessagesError,
        isLoading: allConversationMessagesIsLoading,
    } = useGetAllConversationMessagesQuery({
        conversationId,
        limit: Constants.app.maxMessagesPerRequest,
    });
    const {
        data: conversationParticipants,
        error: conversationParticipantsError,
        isLoading: conversationParticipantsIsLoading,
    } = useGetConversationParticipantsQuery(conversationId);
    const {
        data: assistants,
        error: assistantsError,
        isLoading: assistantsIsLoading,
        refetch: assistantsRefetch,
    } = useGetAssistantsInConversationQuery(conversationId);
    const {
        data: conversationFiles,
        error: conversationFilesError,
        isLoading: conversationFilesIsLoading,
    } = useGetConversationFilesQuery(conversationId);

    const { data: assistantCapabilities, isFetching: assistantCapabilitiesIsFetching } = useGetAssistantCapabilities(
        assistants ?? [],
        { skip: assistantsIsLoading || assistantsError !== undefined },
    );

    const error =
        conversationError ||
        allConversationMessagesError ||
        conversationParticipantsError ||
        assistantsError ||
        conversationFilesError;

    const isLoading =
        conversationIsLoading ||
        allConversationMessagesIsLoading ||
        conversationParticipantsIsLoading ||
        assistantsIsLoading ||
        conversationFilesIsLoading;

    // region Events

    // handler for when a new message is created
    const onMessageCreated = React.useCallback(async () => {
        if (!allConversationMessages) {
            return;
        }

        const lastMessageId = allConversationMessages[allConversationMessages.length - 1]?.id;
        const newMessages = await dispatch(
            conversationApi.endpoints.getAllConversationMessages.initiate({
                conversationId,
                limit: Constants.app.maxMessagesPerRequest,
                after: lastMessageId,
            }),
        ).unwrap();
        const updatedMessages = [...allConversationMessages, ...newMessages];

        // update the cache with the new messages
        dispatch(
            updateGetAllConversationMessagesQueryData(
                { conversationId, limit: Constants.app.maxMessagesPerRequest },
                updatedMessages,
            ),
        );
    }, [allConversationMessages, conversationId, dispatch]);

    // handler for when a message is deleted
    const onMessageDeleted = React.useCallback(
        (messageId: string) => {
            if (!allConversationMessages) {
                return;
            }

            const updatedMessages = allConversationMessages.filter((message) => message.id !== messageId);

            // remove the message from the messages state
            dispatch(
                updateGetAllConversationMessagesQueryData(
                    { conversationId, limit: Constants.app.maxMessagesPerRequest },
                    updatedMessages,
                ),
            );
        },
        [allConversationMessages, conversationId, dispatch],
    );

    // handler for when a new participant is created
    const onParticipantCreated = React.useCallback(
        (participant: ConversationParticipant) =>
            // add the new participant to the cached participants
            dispatch(
                updateGetConversationParticipantsQueryData(conversationId, {
                    participants: [...(conversationParticipants ?? []), participant],
                }),
            ),
        [dispatch, conversationId, conversationParticipants],
    );

    // handler for when a participant is updated
    const onParticipantUpdated = React.useCallback(
        (participant: ConversationParticipant) =>
            // update the participant in the cached participants
            dispatch(
                updateGetConversationParticipantsQueryData(conversationId, {
                    participants: (conversationParticipants ?? []).map((existingParticipant) =>
                        existingParticipant.id === participant.id ? participant : existingParticipant,
                    ),
                }),
            ),
        [dispatch, conversationId, conversationParticipants],
    );

    // subscribe to conversation events
    useConversationEvents(conversationId, {
        onMessageCreated,
        onMessageDeleted,
        onParticipantCreated,
        onParticipantUpdated,
    });

    // endregion

    // region Rewind

    const rewindToBefore = React.useCallback(
        async (message: ConversationMessage, redo: boolean) => {
            if (!allConversationMessages) {
                return;
            }

            // find the index of the message to rewind to
            const messageIndex = allConversationMessages.findIndex(
                (possibleMessage) => possibleMessage.id === message.id,
            );

            // if the message is not found, do nothing
            if (messageIndex === -1) {
                return;
            }

            // delete all messages from the message to the end of the conversation
            for (let i = messageIndex; i < allConversationMessages.length; i++) {
                await dispatch(
                    conversationApi.endpoints.deleteConversationMessage.initiate({
                        conversationId,
                        messageId: allConversationMessages[i].id,
                    }),
                );
            }

            // if redo is true, create a new message with the same content as the message to redo
            if (redo) {
                await dispatch(
                    conversationApi.endpoints.createConversationMessage.initiate({
                        conversationId,
                        ...message,
                    }),
                );
            }
        },
        [allConversationMessages, conversationId, dispatch],
    );

    // endregion

    // add more messages related utility functions here, separated by region if applicable

    return {
        conversation,
        allConversationMessages,
        conversationParticipants,
        assistants,
        conversationFiles,
        assistantCapabilities,
        error,
        isLoading,
        assistantsRefetch,
        assistantCapabilitiesIsFetching,
        rewindToBefore,
    };
};
