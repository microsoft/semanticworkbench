import { ConversationParticipant } from '../../models/ConversationParticipant';
import { workbenchApi } from './workbench';

const participantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConversationParticipants: builder.query<ConversationParticipant[], string>({
            query: (conversationId) => `/conversations/${conversationId}/participants?include_inactive=true`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationParticipants(response),
        }),
        addConversationParticipant: builder.mutation<
            void,
            { conversationId: string; participantId: string; metadata?: Record<string, any> }
        >({
            query: ({ conversationId, participantId, metadata }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { active_participant: true, metadata },
            }),
            invalidatesTags: ['Conversation'],
        }),
        updateConversationParticipant: builder.mutation<
            void,
            { conversationId: string; participantId: string; status?: string; metadata?: Record<string, any> }
        >({
            query: ({ conversationId, participantId, status, metadata }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { status, active_participant: true, metadata },
            }),
            // This mutation should not invalidate the conversation query because it does not add or remove participants
            invalidatesTags: [],
        }),
        removeConversationParticipant: builder.mutation<void, { conversationId: string; participantId: string }>({
            query: ({ conversationId, participantId }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { active_participant: false },
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

// Non-hook helpers

export const updateGetConversationParticipantsQueryData = (conversationId: string, data: any) =>
    participantApi.util.updateQueryData('getConversationParticipants', conversationId, () =>
        transformResponseToConversationParticipants(data),
    );

export const {
    useGetConversationParticipantsQuery,
    useAddConversationParticipantMutation,
    useUpdateConversationParticipantMutation,
    useRemoveConversationParticipantMutation,
} = participantApi;

const transformResponseToConversationParticipants = (response: any): ConversationParticipant[] => {
    try {
        return response.participants.map(transformResponseToConversationParticipant);
    } catch (error) {
        throw new Error(`Failed to transform participants response: ${error}`);
    }
};

export const transformResponseToConversationParticipant = (response: any): ConversationParticipant => {
    try {
        return {
            id: response.id,
            conversationId: response.conversation_id,
            role: response.role,
            name: response.name,
            image: response.image ?? undefined,
            online: response.online ?? undefined,
            status: response.status,
            statusTimestamp: response.status_updated_timestamp,
            conversationPermission: response.conversation_permission,
            active: response.active_participant,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform participant response: ${error}`);
    }
};
