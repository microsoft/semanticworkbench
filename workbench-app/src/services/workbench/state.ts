import { Config } from '../../models/Config';
import { ConversationState } from '../../models/ConversationState';
import { ConversationStateDescription } from '../../models/ConversationStateDescription';
import { updateVSCodeMcpServerUrl } from './updateMcpServerUrl';
import { workbenchApi } from './workbench';

const stateApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getConfig: builder.query<Config, { assistantId: string }>({
            query: ({ assistantId }) => `/assistants/${assistantId}/config`,
            providesTags: ['Config'],
            transformResponse: (response: any) => transformResponseToConfig(response),
        }),
        updateConfig: builder.mutation<Config, { assistantId: string; config: Config }>({
            query: (body) => ({
                url: `/assistants/${body.assistantId}/config`,
                method: 'PUT',
                body: transformConfigForRequest(body.config),
            }),
            invalidatesTags: ['Config'],
            transformResponse: (response: any) => transformResponseToConfig(response),
        }),
        getConversationStateDescriptions: builder.query<
            ConversationStateDescription[],
            { assistantId: string; conversationId: string }
        >({
            query: ({ assistantId, conversationId }) =>
                `/assistants/${assistantId}/conversations/${conversationId}/states`,
            providesTags: ['State'],
            transformResponse: (response: any) =>
                response.states.map((stateDescription: any) => ({
                    id: stateDescription.id,
                    displayName: stateDescription.display_name,
                    description: stateDescription.description,
                })),
        }),
        getConversationState: builder.query<
            ConversationState,
            { assistantId: string; conversationId: string; stateId: string }
        >({
            query: ({ assistantId, conversationId, stateId }) =>
                `/assistants/${assistantId}/conversations/${conversationId}/states/${stateId}`,
            providesTags: ['State'],
            transformResponse: (response: any, _meta, { stateId }) =>
                transformResponseToConversationState(response, stateId),
        }),
        updateConversationState: builder.mutation<
            ConversationState,
            { assistantId: string; conversationId: string; state: ConversationState }
        >({
            query: (body) => ({
                url: `/assistants/${body.assistantId}/conversations/${body.conversationId}/states/${body.state.id}`,
                method: 'PUT',
                body: transformConversationStateForRequest(body.state),
            }),
            invalidatesTags: ['State'],
            transformResponse: (response: any, _meta, { state }) =>
                transformResponseToConversationState(response, state.id),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetConfigQuery,
    useUpdateConfigMutation,
    useGetConversationStateDescriptionsQuery,
    useGetConversationStateQuery,
    useUpdateConversationStateMutation,
} = stateApi;

const transformResponseToConfig = (response: any) => {
    try {
        // Create the config object
        const config = {
            config: response.config,
            jsonSchema: response.json_schema,
            uiSchema: response.ui_schema,
        };

        // Update the VSCode MCP server URL in the config if it exists
        if (config.config) {
            config.config = updateVSCodeMcpServerUrl(config.config);
        }

        return config;
    } catch (error) {
        throw new Error(`Failed to transform config response: ${error}`);
    }
};

const transformConfigForRequest = (config: Config) => {
    // Update the VSCode MCP server URL in the config if it exists
    const updatedConfig = config.config ? updateVSCodeMcpServerUrl(config.config) : config.config;

    return {
        config: updatedConfig,
        json_schema: config.jsonSchema,
        ui_schema: config.uiSchema,
    };
};

const transformResponseToConversationState = (response: any, stateId: string) => {
    try {
        return {
            id: stateId,
            data: response.data,
            jsonSchema: response.json_schema,
            uiSchema: response.ui_schema,
        };
    } catch (error) {
        throw new Error(`Failed to transform conversation state response: ${error}`);
    }
};

const transformConversationStateForRequest = (conversationState: ConversationState) => ({
    data: conversationState.data,
    json_schema: conversationState.jsonSchema,
    ui_schema: conversationState.uiSchema,
});
