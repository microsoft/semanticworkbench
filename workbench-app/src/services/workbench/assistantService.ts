import { AssistantServiceInfo } from '../../models/AssistantServiceInfo';
import {
    AssistantServiceRegistration,
    NewAssistantServiceRegistration,
} from '../../models/AssistantServiceRegistration';
import { workbenchApi } from './workbench';

export const assistantServiceApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getAssistantServiceInfo: builder.query<AssistantServiceInfo, string>({
            query: (assistantServiceId: string) => `/assistant-services/${encodeURIComponent(assistantServiceId)}`,
            providesTags: ['AssistantServiceInfo'],
            transformResponse: (response: any) => transformResponseToAssistantServiceInfo(response),
        }),
        getAssistantServiceInfos: builder.query<AssistantServiceInfo[], { userIds?: string[] }>({
            query: () => `/assistant-services`,
            providesTags: ['AssistantServiceInfo'],
            transformResponse: (response: any) => transformResponseToAssistantServiceInfos(response),
        }),
        getAssistantServiceRegistration: builder.query<AssistantServiceRegistration, string>({
            query: (id) => `/assistant-service-registrations/${encodeURIComponent(id)}`,
            providesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        getAssistantServiceRegistrations: builder.query<
            AssistantServiceRegistration[],
            {
                userIds?: string[];
                onlineOnly?: boolean;
            }
        >({
            query: ({ userIds, onlineOnly }) => {
                const params: Record<string, any> = {};
                if (userIds && userIds.length > 0) {
                    params.user_id = userIds;
                }
                if (onlineOnly) {
                    params.assistant_service_online = true;
                }
                return {
                    url: '/assistant-service-registrations',
                    params,
                };
            },
            providesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) =>
                response.assistant_service_registrations.map(transformResponseToAssistantServiceRegistration),
        }),
        createAssistantServiceRegistration: builder.mutation<
            AssistantServiceRegistration,
            NewAssistantServiceRegistration
        >({
            query: (body) => ({
                url: '/assistant-service-registrations',
                method: 'POST',
                body: transformRequestToAssistantServiceRegistration(body),
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        removeAssistantServiceRegistration: builder.mutation<{ id: string }, string>({
            query: (id) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
        }),
        updateAssistantServiceRegistration: builder.mutation<
            AssistantServiceRegistration,
            {
                id: string;
                assistantServiceRegistration: Partial<AssistantServiceRegistration> &
                    Pick<AssistantServiceRegistration, 'name' | 'description' | 'includeInListing'>;
            }
        >({
            query: ({ id, assistantServiceRegistration }) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}`,
                method: 'PATCH',
                body: {
                    name: assistantServiceRegistration.name,
                    description: assistantServiceRegistration.description,
                    include_in_listing: assistantServiceRegistration.includeInListing,
                },
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
        resetAssistantServiceRegistrationApiKey: builder.mutation<AssistantServiceRegistration, string>({
            query: (id) => ({
                url: `/assistant-service-registrations/${encodeURIComponent(id)}/api-key`,
                method: 'POST',
            }),
            invalidatesTags: ['AssistantServiceRegistration'],
            transformResponse: (response: any) => transformResponseToAssistantServiceRegistration(response),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetAssistantServiceInfoQuery,
    useGetAssistantServiceInfosQuery,
    useGetAssistantServiceRegistrationQuery,
    useGetAssistantServiceRegistrationsQuery,
    useCreateAssistantServiceRegistrationMutation,
    useRemoveAssistantServiceRegistrationMutation,
    useUpdateAssistantServiceRegistrationMutation,
    useResetAssistantServiceRegistrationApiKeyMutation,
} = assistantServiceApi;

const transformResponseToAssistantServiceInfo = (response: any): AssistantServiceInfo => ({
    assistantServiceId: response.assistant_service_id,
    templates: response.templates.map((template: any) => ({
        id: template.id,
        name: template.name,
        description: template.description,
        config: {
            config: template.config.config,
            jsonSchema: template.config.json_schema,
            uiSchema: template.config.ui_schema,
        },
    })),
    metadata: response.metadata,
});

const transformResponseToAssistantServiceInfos = (response: any): AssistantServiceInfo[] =>
    (response.assistant_service_infos || []).map(transformResponseToAssistantServiceInfo);

const transformResponseToAssistantServiceRegistration = (response: any): AssistantServiceRegistration => ({
    assistantServiceId: response.assistant_service_id,
    assistantServiceOnline: response.assistant_service_online,
    assistantServiceUrl: response.assistant_service_url,
    name: response.name,
    description: response.description,
    includeInListing: response.include_in_listing,
    createdDateTime: response.create_date_time,
    createdByUserId: response.created_by_user_id,
    createdByUserName: response.created_by_user_name,
    apiKeyName: response.api_key_name,
    apiKey: response.api_key,
});

const transformRequestToAssistantServiceRegistration = (request: NewAssistantServiceRegistration): any => ({
    assistant_service_id: request.assistantServiceId,
    name: request.name,
    description: request.description,
    include_in_listing: request.includeInListing,
});
