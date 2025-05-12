import { Conversation } from '../../models/Conversation';
import { ConversationMessage, conversationMessageFromJSON } from '../../models/ConversationMessage';
import { ConversationMessageDebug, conversationMessageDebugFromJSON } from '../../models/ConversationMessageDebug';
import { transformResponseToConversationParticipant } from './participant';
import { workbenchApi } from './workbench';

interface GetConversationMessagesProps {
    conversationId: string;
    messageTypes?: string[];
    participantRoles?: string[];
    participantIds?: string[];
    before?: string;
    after?: string;
    limit?: number;
}

export const conversationApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        createConversation: builder.mutation<Conversation, Partial<Conversation>>({
            query: (body) => ({
                url: '/conversations',
                method: 'POST',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversation(response),
        }),
        duplicateConversation: builder.mutation<
            { conversationIds: string[]; assistantIds: string[] },
            Pick<Conversation, 'id' | 'title'>
        >({
            query: (body) => ({
                url: `/conversations/${body.id}`,
                method: 'POST',
                body: transformConversationForRequest(body),
            }),
            invalidatesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToImportResult(response),
        }),
        updateConversation: builder.mutation<Conversation, Partial<Conversation> & Pick<Conversation, 'id'>>({
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
        getConversationMessages: builder.query<ConversationMessage[], GetConversationMessagesProps>({
            query: ({
                conversationId,
                messageTypes = ['chat', 'log', 'note', 'notice', 'command', 'command-response'],
                participantRoles,
                participantIds,
                before,
                after,
                limit,
            }) => {
                const params = new URLSearchParams();

                // Append parameters to the query string, one by one for arrays
                messageTypes?.forEach((type) => params.append('message_type', type));
                participantRoles?.forEach((role) => params.append('participant_role', role));
                participantIds?.forEach((id) => params.append('participant_id', id));

                if (before) {
                    params.set('before', before);
                }
                if (after) {
                    params.set('after', after);
                }
                // Ensure limit does not exceed 500
                if (limit !== undefined) {
                    params.set('limit', String(Math.min(limit, 500)));
                }

                return `/conversations/${conversationId}/messages?${params.toString()}`;
            },
            providesTags: ['Conversation'],
            transformResponse: (response: any) => transformResponseToConversationMessages(response),
        }),
        getAllConversationMessages: builder.query<ConversationMessage[], GetConversationMessagesProps>({
            async queryFn(
                {
                    conversationId,
                    messageTypes = ['chat', 'log', 'note', 'notice', 'command', 'command-response'],
                    participantRoles,
                    participantIds,
                    before,
                    after,
                    limit,
                },
                _queryApi,
                _extraOptions,
                fetchWithBQ,
            ) {
                let allMessages: ConversationMessage[] = [];
                let updatedBefore = before;

                while (true) {
                    const params = new URLSearchParams();

                    // Append parameters to the query string, one by one for arrays
                    messageTypes?.forEach((type) => params.append('message_type', type));
                    participantRoles?.forEach((role) => params.append('participant_role', role));
                    participantIds?.forEach((id) => params.append('participant_id', id));

                    if (updatedBefore) {
                        params.set('before', updatedBefore);
                    }
                    if (after) {
                        params.set('after', after);
                    }
                    // Ensure limit does not exceed 500
                    if (limit !== undefined) {
                        params.set('limit', String(Math.min(limit, 500)));
                    }

                    const url = `/conversations/${conversationId}/messages?${params.toString()}`;

                    const response = await fetchWithBQ(url);
                    if (response.error) {
                        return { error: response.error };
                    }

                    const messages: ConversationMessage[] = transformResponseToConversationMessages(response.data);
                    allMessages = [...allMessages, ...messages];

                    if (messages.length !== limit) {
                        break;
                    }

                    updatedBefore = messages[0].id;
                }

                return { data: allMessages };
            },
            providesTags: ['Conversation'],
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
    conversationApi.util.updateQueryData('getConversationMessages', { conversationId }, () => data);

export const {
    useCreateConversationMutation,
    useDuplicateConversationMutation,
    useUpdateConversationMutation,
    useGetConversationsQuery,
    useGetAssistantConversationsQuery,
    useGetConversationQuery,
    useGetConversationMessagesQuery,
    useGetAllConversationMessagesQuery,
    useGetConversationMessageDebugDataQuery,
    useCreateConversationMessageMutation,
    useDeleteConversationMessageMutation,
} = conversationApi;

export const updateGetAllConversationMessagesQueryData = (
    options: GetConversationMessagesProps,
    messages: ConversationMessage[],
) => conversationApi.util.updateQueryData('getAllConversationMessages', options, () => messages);

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

const transformResponseToImportResult = (response: any): { conversationIds: string[]; assistantIds: string[] } => {
    try {
        return {
            conversationIds: response.conversation_ids,
            assistantIds: response.assistant_ids,
        };
    } catch (error) {
        throw new Error(`Failed to transform import result response: ${error}`);
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
