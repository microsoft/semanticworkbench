import { ConversationParticipant } from '../../models/ConversationParticipant';
import { workbenchApi } from './workbench';

const participantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConversationParticipantMe: builder.query<ConversationParticipant | undefined, string>({
            query: (conversationId) => `/conversations/${conversationId}/participants/me?include_inactive=true`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationParticipant(response),
        }),
        getConversationParticipants: builder.query<ConversationParticipant[], string>({
            query: (conversationId) => `/conversations/${conversationId}/participants?include_inactive=true`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationParticipants(response),
        }),
        addConversationParticipant: builder.mutation<void, { conversationId: string; participantId: string }>({
            query: ({ conversationId, participantId }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { active_participant: true },
            }),
            invalidatesTags: ['Conversation'],
        }),
        updateConversationParticipant: builder.mutation<
            void,
            { conversationId: string; participantId: string; status: string }
        >({
            query: ({ conversationId, participantId, status }) => ({
                url: `/conversations/${conversationId}/participants/${participantId}`,
                method: 'PUT',
                body: { status, active_participant: true },
            }),
            invalidatesTags: ['Conversation'],
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
    useGetConversationParticipantMeQuery,
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

const transformResponseToConversationParticipant = (response: any): ConversationParticipant => {
    try {
        return {
            id: response.id,
            role: response.role,
            name: response.name,
            online: response.online ?? undefined,
            status: response.status,
            statusTimestamp: response.status_updated_timestamp,
            conversationPermission: response.conversation_permission,
            active: response.active_participant,
        };
    } catch (error) {
        throw new Error(`Failed to transform participant response: ${error}`);
    }
};
