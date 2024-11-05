import { Conversation } from '../../models/Conversation';
import { ConversationMessage, conversationMessageFromJSON } from '../../models/ConversationMessage';
import { ConversationMessageDebug, conversationMessageDebugFromJSON } from '../../models/ConversationMessageDebug';
import { transformResponseToConversationParticipant } from './participant';
import { workbenchApi } from './workbench';

export const conversationApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        createConversation: builder.mutation<Conversation, Partial<Conversation> & Pick<Conversation, 'title'>>({
            query: (body) => ({
                url: '/conversations',
                method: 'POST',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        updateConversation: builder.mutation<Conversation, Pick<Conversation, 'id' | 'title' | 'metadata'>>({
            query: (body) => ({
                url: `/conversations/${body.id}`,
                method: 'PATCH',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        getConversations: builder.query<Conversation[], void>({
            query: () => '/conversations',
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.conversations.map(transformResponseToConversation),
        }),
        getAssistantConversations: builder.query<Conversation[], string>({
            query: (id) => `/assistants/${id}/conversations`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => response.conversations.map(transformResponseToConversation),
        }),
        getConversation: builder.query<Conversation, string>({
            query: (id) => `/conversations/${id}`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        getConversationMessages: builder.query<ConversationMessage[], string>({
            query: (id) =>
                `/conversations/${id}/messages?message_type=chat&message_type=note&message_type=notice&message_type=command&message_type=command-response`,
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationMessages(response),
        }),
        getConversationMessageDebugData: builder.query<
            ConversationMessageDebug,
            { conversationId: string; messageId: string }
        >({
            query: ({ conversationId, messageId }) =>
                `/conversations/${conversationId}/messages/${messageId}/debug_data`,
            transformResponse: (response: any) => transformResponseToConversationMessageDebug(response),
        }),
        createConversationMessage: builder.mutation<
            ConversationMessage,
            { conversationId: string } & Partial<ConversationMessage> &
                Pick<ConversationMessage, 'content' | 'messageType' | 'metadata'>
        >({
            query: (input) => ({
                url: `/conversations/${input.conversationId}/messages`,
                method: 'POST',
                body: transformMessageForRequest(input),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToMessage(response),
        }),
        deleteConversationMessage: builder.mutation<void, { conversationId: string; messageId: string }>({
            query: ({ conversationId, messageId }) => ({
                url: `/conversations/${conversationId}/messages/${messageId}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['Conversation'],
        }),
    }),
    overrideExisting: false,
});

// Non-hook helpers

export const updateGetConversationMessagesQueryData = (conversationId: string, data: ConversationMessage[]) =>
    conversationApi.util.updateQueryData('getConversationMessages', conversationId, () => data);

export const {
    useCreateConversationMutation,
    useUpdateConversationMutation,
    useGetConversationsQuery,
    useGetAssistantConversationsQuery,
    useGetConversationQuery,
    useGetConversationMessagesQuery,
    useGetConversationMessageDebugDataQuery,
    useCreateConversationMessageMutation,
    useDeleteConversationMessageMutation,
} = conversationApi;

const transformConversationForRequest = (conversation: Partial<Conversation>) => ({
    id: conversation.id,
    title: conversation.title,
    metadata: conversation.metadata,
});

const transformResponseToConversation = (response: any): Conversation => {
    try {
        return {
            id: response.id,
            ownerId: response.owner_id,
            title: response.title,
            created: response.created_datetime,
            latest_message: response.latest_message ? transformResponseToMessage(response.latest_message) : undefined,
            participants: response.participants.map(transformResponseToConversationParticipant),
            metadata: response.metadata,
            conversationPermission: response.conversation_permission,
            importedFromConversationId: response.imported_from_conversation_id,
        };
    } catch (error) {
        throw new Error(`Failed to transform conversation response: ${error}`);
    }
};

const transformResponseToConversationMessages = (response: any): ConversationMessage[] => {
    try {
        return response.messages.map(transformResponseToMessage);
    } catch (error) {
        throw new Error(`Failed to transform messages response: ${error}`);
    }
};

const transformResponseToMessage = (response: any): ConversationMessage => {
    try {
        return conversationMessageFromJSON(response);
    } catch (error) {
        throw new Error(`Failed to transform message response: ${error}`);
    }
};

const transformResponseToConversationMessageDebug = (response: any): ConversationMessageDebug => {
    try {
        return conversationMessageDebugFromJSON(response);
    } catch (error) {
        throw new Error(`Failed to transform message debug response: ${error}`);
    }
};

const transformMessageForRequest = (message: Partial<ConversationMessage>) => {
    const request: Record<string, any> = {
        timestamp: message.timestamp,
        content: message.content,
        message_type: message.messageType,
        content_type: message.contentType,
        filenames: message.filenames,
        metadata: message.metadata,
    };

    if (message.sender) {
        request.sender = {
            participant_id: message.sender.participantId,
            participant_role: message.sender.participantRole,
        };
    }

    return request;
};
