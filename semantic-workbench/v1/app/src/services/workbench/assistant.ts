import { Assistant } from '../../models/Assistant';
import { AssistantServiceInfo } from '../../models/AssistantServiceInfo';
import { workbenchApi } from './workbench';

export const assistantApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAssistantServiceInfo: builder.query<AssistantServiceInfo, string>({
            query: (assistantServiceId: string) => `/assistant-services/${encodeURIComponent(assistantServiceId)}/info`,
            providesTags: ['AssistantServiceInfo'],
            transformResponse: (response: any) => transformResponseToAssistantServiceDescription(response),
        }),
        getAssistants: builder.query<Assistant[], void>({
            query: () => '/assistants',
            providesTags: ['Assistant'],
            transformResponse: (response: any) => response.assistants.map(transformResponseToAssistant),
        }),
        getAssistant: builder.query<Assistant, string>({
            query: (id) => `/assistants/${id}`,
            providesTags: ['Assistant'],
            transformResponse: (response: any) => transformResponseToAssistant(response),
        }),
        createAssistant: builder.mutation<
            Assistant,
            Partial<Assistant> & Pick<Assistant, 'name' | 'assistantServiceId'>
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
            invalidatesTags: ['Assistant'],
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetAssistantServiceInfoQuery,
    useGetAssistantsQuery,
    useGetAssistantQuery,
    useCreateAssistantMutation,
    useUpdateAssistantMutation,
    useDeleteAssistantMutation,
} = assistantApi;

const transformResponseToAssistantServiceDescription = (response: any): AssistantServiceInfo => ({
    defaultConfig: {
        config: response.default_config.config,
        jsonSchema: response.default_config.json_schema,
        uiSchema: response.default_config.ui_schema,
    },
});

const transformAssistantForRequest = (assistant: Partial<Assistant>) => ({
    id: assistant.id,
    name: assistant.name,
    assistant_service_id: assistant.assistantServiceId,
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
