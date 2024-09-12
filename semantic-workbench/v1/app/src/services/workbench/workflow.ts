import { Assistant } from '../../models/Assistant';
import { WorkflowDefinition } from '../../models/WorkflowDefinition';
import { WorkflowRun } from '../../models/WorkflowRun';
import { transformResponseToAssistant } from './assistant';
import { workbenchApi } from './workbench';

export const workflowApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        getWorkflowDefinitionDefaults: builder.query<Omit<WorkflowDefinition, 'id'>, void>({
            query: () => '/workflow-definitions/defaults',
            transformResponse: (response: any) => transformResponseToWorkflowDefinitionWithoutId(response),
        }),
        getWorkflowDefinitions: builder.query<WorkflowDefinition[], void>({
            query: () => '/workflow-definitions',
            providesTags: ['WorkflowDefinition'],
            transformResponse: (response: any) =>
                response.workflow_definitions.map(transformResponseToWorkflowDefinition),
        }),
        getWorkflowDefinition: builder.query<WorkflowDefinition | null, string>({
            query: (id) => `/workflow-definitions/${id}`,
            providesTags: ['WorkflowDefinition'],
            transformResponse: (response: any) => transformResponseToWorkflowDefinition(response),
        }),
        createWorkflowDefinition: builder.mutation<WorkflowDefinition, Omit<WorkflowDefinition, 'id'>>({
            query: (workflowDefinition) => ({
                url: `/workflow-definitions`,
                method: 'POST',
                body: transformWorkflowDefinitionForRequest(workflowDefinition),
            }),
            invalidatesTags: ['WorkflowDefinition'],
            transformResponse: (response: any) => transformResponseToWorkflowDefinition(response),
        }),
        updateWorkflowDefinition: builder.mutation<
            WorkflowDefinition,
            Partial<WorkflowDefinition> & Pick<WorkflowDefinition, 'id'>
        >({
            query: (workflowDefinition) => ({
                url: `/workflow-definitions/${workflowDefinition.id}`,
                method: 'PATCH',
                body: transformWorkflowDefinitionForRequest(workflowDefinition),
            }),
            invalidatesTags: ['WorkflowDefinition'],
        }),
        updateWorkflowDefinitionParticipant: builder.mutation<
            string,
            { workflowDefinitionId: string; participantId: string; active: boolean }
        >({
            query: ({ workflowDefinitionId, participantId, active }) => ({
                url: `/workflow-definitions/${workflowDefinitionId}/participants/${participantId}`,
                method: 'PATCH',
                body: { active_participant: active },
            }),
            invalidatesTags: ['WorkflowDefinition'],
        }),
        getWorkflowRuns: builder.query<WorkflowRun[], string | void>({
            query: (workflowDefinitionId) =>
                workflowDefinitionId
                    ? `/workflow-runs?workflow_definition_id=${workflowDefinitionId}`
                    : '/workflow-runs',
            providesTags: ['WorkflowRun'],
            transformResponse: (response: any) => response.workflow_runs.map(transformResponseToWorkflowRun),
        }),
        getWorkflowRun: builder.query<WorkflowRun | null, string>({
            query: (workflowRunId) => `/workflow-runs/${workflowRunId}`,
            providesTags: ['WorkflowRun'],
            transformResponse: (response: any) => transformResponseToWorkflowRun(response),
        }),
        createWorkflowRun: builder.mutation<
            WorkflowRun,
            Partial<WorkflowRun> & Pick<WorkflowRun, 'title' | 'workflowDefinitionId'>
        >({
            query: (workflowRun) => ({
                url: `/workflow-runs`,
                method: 'POST',
                body: transformWorkflowRunForRequest(workflowRun),
            }),
            invalidatesTags: ['WorkflowRun'],
            transformResponse: (response: any) => transformResponseToWorkflowRun(response),
        }),
        updateWorkflowRun: builder.mutation<WorkflowRun, Partial<WorkflowRun> & Pick<WorkflowRun, 'id'>>({
            query: (workflowRun) => ({
                url: `/workflow-runs/${workflowRun.id}`,
                method: 'PATCH',
                body: transformWorkflowRunForRequest(workflowRun),
            }),
            invalidatesTags: ['WorkflowRun'],
            transformResponse: (response: any) => transformResponseToWorkflowRun(response),
        }),
        getWorkflowRunAssistants: builder.query<Assistant[], string>({
            query: (workflowRunId) => `/workflow-runs/${workflowRunId}/assistants`,
            providesTags: ['Assistant', 'WorkflowRun'],
            transformResponse: (response: any) => transformResponseToWorkflowRunAssistants(response),
        }),
        switchWorkflowRunState: builder.mutation<WorkflowRun, { workflowRunId: string; stateId: string }>({
            query: ({ workflowRunId, stateId }) => ({
                url: `/workflow-runs/${workflowRunId}/switch-state`,
                method: 'POST',
                body: { state_id: stateId },
            }),
            invalidatesTags: ['WorkflowRun'],
            transformResponse: (response: any) => transformResponseToWorkflowRun(response),
        }),
        deleteWorkflowRun: builder.mutation<string, string>({
            query: (workflowRunId) => ({
                url: `/workflow-runs/${workflowRunId}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['WorkflowRun'],
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetWorkflowDefinitionDefaultsQuery,
    useGetWorkflowDefinitionsQuery,
    useGetWorkflowDefinitionQuery,
    useCreateWorkflowDefinitionMutation,
    useUpdateWorkflowDefinitionMutation,
    useUpdateWorkflowDefinitionParticipantMutation,
    useGetWorkflowRunQuery,
    useGetWorkflowRunsQuery,
    useCreateWorkflowRunMutation,
    useUpdateWorkflowRunMutation,
    useGetWorkflowRunAssistantsQuery,
    useSwitchWorkflowRunStateMutation,
    useDeleteWorkflowRunMutation,
} = workflowApi;

const transformWorkflowDefinitionForRequest = (workflowDefinition: Partial<WorkflowDefinition>) => ({
    id: workflowDefinition.id,
    label: workflowDefinition.label,
    start_state_id: workflowDefinition.startStateId,
    states: workflowDefinition.states?.map((state) => ({
        id: state.id,
        label: state.label,
        conversation_definition_id: state.conversationDefinitionId,
        force_new_conversation_instance: state.forceNewConversationInstance ?? false,
        assistant_data_list: state.assistantDataList.map((assistantData) => ({
            assistant_definition_id: assistantData.assistantDefinitionId,
            config_data: assistantData.configData,
        })),
        editor_data: state.editorData,
        outlets: state.outlets.map((outlet) => ({
            id: outlet.id,
            label: outlet.label,
            prompts: {
                evaluate_transition: outlet.prompts.evaluateTransition,
                context_transfer: outlet.prompts.contextTransfer,
            },
        })),
    })),
    transitions: workflowDefinition.transitions?.map((transition) => ({
        id: transition.id,
        source_outlet_id: transition.sourceOutletId,
        target_state_id: transition.targetStateId,
    })),
    conversation_definitions: workflowDefinition.definitions?.conversations?.map((conversationDefinition) => ({
        id: conversationDefinition.id,
        title: conversationDefinition.title,
    })),
    assistant_definitions: workflowDefinition.definitions?.assistants.map((assistantDefinition) => ({
        id: assistantDefinition.id,
        name: assistantDefinition.name,
        assistant_service_id: assistantDefinition.assistantServiceId,
    })),
    context_transfer_instruction: workflowDefinition.instructions?.contextTransfer,
});

const transformResponseToWorkflowDefinitionWithoutId = (response: any): Omit<WorkflowDefinition, 'id'> => {
    try {
        return {
            label: response.label,
            startStateId: response.start_state_id,
            states: response.states.map((state: any) => ({
                id: state.id,
                label: state.label,
                conversationDefinitionId: state.conversation_definition_id,
                forceNewConversationInstance: state.force_new_conversation_instance,
                assistantDataList: state.assistant_data_list.map((assistantData: any) => ({
                    assistantDefinitionId: assistantData.assistant_definition_id,
                    configData: assistantData.config_data,
                })),
                editorData: state.editor_data,
                outlets: state.outlets.map((outlet: any) => ({
                    id: outlet.id,
                    label: outlet.label,
                    prompts: {
                        evaluateTransition: outlet.prompts.evaluate_transition,
                        contextTransfer: outlet.prompts.context_transfer,
                    },
                })),
            })),
            transitions: response.transitions.map((transition: any) => ({
                id: transition.id,
                sourceOutletId: transition.source_outlet_id,
                targetStateId: transition.target_state_id,
            })),
            definitions: {
                conversations: response.conversation_definitions.map((conversationDefinition: any) => ({
                    id: conversationDefinition.id,
                    title: conversationDefinition.title,
                })),
                assistants: response.assistant_definitions.map((assistantDefinition: any) => ({
                    id: assistantDefinition.id,
                    name: assistantDefinition.name,
                    assistantServiceId: assistantDefinition.assistant_service_id,
                })),
            },
            instructions: {
                contextTransfer: response.context_transfer_instruction,
            },
        };
    } catch (error) {
        throw new Error(`Failed to transform workflow response: ${error}`);
    }
};

const transformResponseToWorkflowDefinition = (response: any): WorkflowDefinition => {
    try {
        return {
            id: response.id,
            ...transformResponseToWorkflowDefinitionWithoutId(response),
        };
    } catch (error) {
        throw new Error(`Failed to transform workflow response: ${error}`);
    }
};

const transformWorkflowRunForRequest = (workflowRun: Partial<WorkflowRun>) => ({
    id: workflowRun.id,
    title: workflowRun.title,
    workflow_definition_id: workflowRun.workflowDefinitionId,
    current_state_id: workflowRun.currentStateId,
    conversation_mappings: workflowRun.conversationMappings?.map((conversationMapping) => ({
        conversation_id: conversationMapping.conversationId,
        conversation_definition_id: conversationMapping.conversationDefinitionId,
    })),
    assistant_mappings: workflowRun.assistantMappings?.map((assistantMapping) => ({
        assistant_id: assistantMapping.assistantId,
        conversation_id: assistantMapping.conversationId,
    })),
    metadata: workflowRun.metadata,
});

const transformResponseToWorkflowRun = (response: any): WorkflowRun => {
    try {
        return {
            id: response.id,
            title: response.title,
            workflowDefinitionId: response.workflow_definition_id,
            currentStateId: response.current_state_id,
            conversationMappings: response.conversation_mappings.map((conversationMapping: any) => ({
                conversationId: conversationMapping.conversation_id,
                conversationDefinitionId: conversationMapping.conversation_definition_id,
            })),
            assistantMappings: response.assistant_mappings.map((assistantMapping: any) => ({
                assistantId: assistantMapping.assistant_id,
                conversationId: assistantMapping.conversation_id,
            })),
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform workflow run response: ${error}`);
    }
};

const transformResponseToWorkflowRunAssistants = (response: any): Assistant[] => {
    try {
        return response.assistants.map(transformResponseToAssistant);
    } catch (error) {
        throw new Error(`Failed to transform workflow run assistants response: ${error}`);
    }
};
