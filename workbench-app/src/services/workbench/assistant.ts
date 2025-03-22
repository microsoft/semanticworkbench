import { Assistant } from '../../models/Assistant';
import { workbenchApi } from './workbench';

export const assistantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAssistants: builder.query<Assistant[], void>({
            query: () => '/assistants',
            providesTags: ['Assistant'],
            transformResponse: (response: any) => response.assistants.map(transformResponseToAssistant),
        }),
        getAssistantsInConversation: builder.query<Assistant[], string>({
            query: (conversationId: string) => `/assistants?conversation_id=${conversationId}`,
            providesTags: ['Assistant', 'Conversation'],
            transformResponse: (response: any) => response.assistants.map(transformResponseToAssistant),
        }),
        getAssistant: builder.query<Assistant, string>({
            query: (id) => `/assistants/${id}`,
            providesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        createAssistant: builder.mutation<
            Assistant,
            Partial<Assistant> & Pick<Assistant, 'name' | 'assistantServiceId' | 'templateId'>
        >({
            query: (body) => ({
                url: '/assistants',
                method: 'POST',
                body: transformAssistantForRequest(body),
            }),
            invalidatesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        updateAssistant: builder.mutation<Assistant, Assistant>({
            query: (body) => ({
                url: `/assistants/${body.id}`,
                method: 'PATCH',
                body: transformAssistantForRequest(body),
            }),
            invalidatesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        deleteAssistant: builder.mutation<{ id: string }, string>({
            query: (id) => ({
                url: `/assistants/${id}`,
                method: 'DELETE',
            }),
            // deleting an assistant can remove it from 0 or more conversations
            invalidatesTags: ['Assistant', 'Conversation'],
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetAssistantsQuery,
    useGetAssistantsInConversationQuery,
    useGetAssistantQuery,
    useCreateAssistantMutation,
    useUpdateAssistantMutation,
    useDeleteAssistantMutation,
} = assistantApi;

const transformAssistantForRequest = (assistant: Partial<Assistant>) => ({
    id: assistant.id,
    name: assistant.name,
    assistant_service_id: assistant.assistantServiceId,
    template_id: assistant.templateId,
    metadata: assistant.metadata,
});

export const transformResponseToAssistant = (response: any): Assistant => {
    try {
        return {
            id: response.id,
            name: response.name,
            image: response.image,
            assistantServiceId: response.assistant_service_id,
            createdDatetime: response.created_datetime,
            templateId: response.template_id,
            conversations: {
                ...Object.fromEntries(
                    Object.entries(response.conversations ?? {}).map(
                        ([conversationId, conversation]: [string, any]) => [
                            conversationId,
                            {
                                id: conversation.id,
                            },
                        ],
                    ),
                ),
            },
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform assistant response: ${error}`);
    }
};
