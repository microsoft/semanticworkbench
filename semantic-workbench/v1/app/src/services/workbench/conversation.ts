import { Conversation } from '../../models/Conversation';
import { ConversationMessage } from '../../models/ConversationMessage';
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
        updateConversation: builder.mutation<Conversation, Conversation>({
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
        createConversationMessage: builder.mutation<
            ConversationMessage,
            { conversationId: string; content: string; messageType?: string; metadata?: Record<string, any> }
        >({
            query: ({ conversationId, content, messageType, metadata }) => ({
                url: `/conversations/${conversationId}/messages`,
                method: 'POST',
                body: { content, message_type: messageType ?? 'chat', metadata },
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
            title: response.title,
            metadata: response.metadata,
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
        return {
            id: response.id,
            sender: {
                participantId: response.sender.participant_id,
                participantRole: response.sender.participant_role,
            },
            timestamp: response.timestamp,
            messageType: response.message_type ?? 'chat',
            content: response.content,
            contentType: response.content_type,
            filenames: response.filenames,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform message response: ${error}`);
    }
};
