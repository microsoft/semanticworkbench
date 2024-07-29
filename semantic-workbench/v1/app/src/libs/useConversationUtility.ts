// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Assistant } from '../models/Assistant';
import {
    useGetAssistantsQuery,
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
} from '../services/workbench';

export const useConversationUtility = (conversationId: string) => {
    const [conversationAssistants, setConversationAssistants] = React.useState<Assistant[]>();
    const [error, setError] = React.useState<string>();
    const [isLoading, setIsLoading] = React.useState<boolean>(true);

    // Get the conversation
    const {
        data: conversation,
        error: conversationError,
        isLoading: isLoadingConversation,
        refetch: refetchConversation,
    } = useGetConversationQuery(conversationId);

    // Get participants
    const {
        data: participants,
        error: participantsError,
        isLoading: isLoadingParticipants,
        refetch: refetchParticipants,
    } = useGetConversationParticipantsQuery(conversationId);

    // Get all assistants
    const {
        data: assistants,
        error: assistantsError,
        isLoading: isLoadingAssistants,
        refetch: refetchAssistants,
    } = useGetAssistantsQuery();

    const refetch = React.useCallback(async () => {
        await refetchConversation();
        await refetchParticipants();
        await refetchAssistants();
    }, [refetchAssistants, refetchParticipants, refetchConversation]);

    // Set error state if there are any errors
    React.useEffect(() => {
        if (assistantsError) {
            const errorMessage = JSON.stringify(assistantsError);
            setError(`Error loading assistants: ${errorMessage}`);
        }

        if (conversationError) {
            const errorMessage = JSON.stringify(conversationError);
            setError(`Error loading conversation: ${errorMessage}`);
        }

        if (participantsError) {
            const errorMessage = JSON.stringify(participantsError);
            setError(`Error loading participants: ${errorMessage}`);
        }

        if (!isLoadingAssistants && !assistants) {
            const errorMessage = `No assistants loaded`;
            setError(errorMessage);
        }

        if (!isLoadingConversation && !conversation) {
            const errorMessage = `No conversation loaded for ${conversationId}`;
            setError(errorMessage);
        }

        if (!isLoadingParticipants && !participants) {
            const errorMessage = `No participants loaded for ${conversationId}`;
            setError(errorMessage);
        }
    }, [
        assistants,
        assistantsError,
        conversation,
        conversationError,
        participants,
        participantsError,
        conversationId,
        isLoadingAssistants,
        isLoadingConversation,
        isLoadingParticipants,
    ]);

    // Set loading state
    React.useEffect(() => {
        if (!isLoadingAssistants && !isLoadingConversation && !isLoadingParticipants) {
            if (isLoading) {
                setIsLoading(false);
            }
        } else {
            if (!isLoading) {
                setIsLoading(true);
            }
        }
    }, [isLoading, isLoadingAssistants, isLoadingConversation, isLoadingParticipants]);

    // Set conversation assistants
    React.useEffect(() => {
        if (
            !isLoadingConversation &&
            conversation &&
            !isLoadingAssistants &&
            assistants &&
            !isLoadingParticipants &&
            participants
        ) {
            const filteredAssistants = assistants.filter((assistant) =>
                participants.find((participant) => participant.id === assistant.id),
            );
            setConversationAssistants(filteredAssistants);
        } else {
            if (conversationAssistants) {
                setConversationAssistants(undefined);
            }
        }
    }, [
        assistants,
        conversation,
        participants,
        conversationAssistants,
        conversationId,
        isLoadingAssistants,
        isLoadingConversation,
        isLoadingParticipants,
    ]);

    return {
        conversation,
        conversationAssistants,
        error,
        isLoading,
        refetch,
    };
};
