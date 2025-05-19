import React from 'react';
import { Constants } from '../Constants';
import { Assistant } from '../models/Assistant';
import { AssistantServiceInfo, AssistantTemplate } from '../models/AssistantServiceInfo';
import { useAppSelector } from '../redux/app/hooks';
import {
    useAddConversationParticipantMutation,
    useCreateAssistantMutation,
    useCreateConversationMessageMutation,
    useCreateConversationMutation,
    useGetAssistantServiceInfosQuery,
    useGetAssistantsQuery,
    useLazyGetConversationQuery,
} from '../services/workbench';

export interface AssistantServiceTemplate {
    service: AssistantServiceInfo;
    template: AssistantTemplate;
}

export const useCreateConversation = () => {
    const {
        data: assistants,
        error: assistantsError,
        isLoading: assistantsLoading,
        refetch: refetchAssistants,
    } = useGetAssistantsQuery();
    const {
        data: assistantServices,
        error: assistantServicesError,
        isLoading: assistantServicesLoading,
    } = useGetAssistantServiceInfosQuery({});
    const {
        data: myAssistantServices,
        error: myAssistantServicesError,
        isLoading: myAssistantServicesLoading,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });

    const [createAssistant] = useCreateAssistantMutation();
    const [createConversation] = useCreateConversationMutation();
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [getConversation] = useLazyGetConversationQuery();

    const [isFetching, setIsFetching] = React.useState(true);
    const localUserName = useAppSelector((state) => state.localUser.name);

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (assistantServicesError) {
        const errorMessage = JSON.stringify(assistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }

    if (myAssistantServicesError) {
        const errorMessage = JSON.stringify(myAssistantServicesError);
        throw new Error(`Error loading my assistant services: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (isFetching && !assistantsLoading && !assistantServicesLoading && !myAssistantServicesLoading) {
            setIsFetching(false);
        }

        if (!isFetching && (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading)) {
            setIsFetching(true);
        }
    }, [assistantsLoading, assistantServicesLoading, myAssistantServicesLoading, isFetching]);

    const create = React.useCallback(
        async (
            conversationInfo:
                | {
                      assistantId: string;
                      conversationMetadata?: { [key: string]: any };
                      participantMetadata?: { [key: string]: any };
                      additionalAssistantIds?: string[];
                      existingConversationId?: string;
                  }
                | {
                      name: string;
                      assistantServiceId: string;
                      templateId: string;
                      conversationMetadata?: { [key: string]: any };
                      participantMetadata?: { [key: string]: any };
                      additionalAssistantIds?: string[];
                      existingConversationId?: string;
                  },
        ) => {
            if (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading) {
                throw new Error('Cannot create conversation while loading assistants or assistant services');
            }

            let assistant: Assistant | undefined = undefined;

            const conversation = conversationInfo.existingConversationId
                ? await getConversation(conversationInfo.existingConversationId).unwrap()
                : await createConversation({ metadata: conversationInfo.conversationMetadata }).unwrap();

            if ('assistantId' in conversationInfo) {
                assistant = assistants?.find((a) => a.id === conversationInfo.assistantId);
                if (!assistant) {
                    throw new Error('Assistant not found');
                }
            } else {
                const { name, assistantServiceId, templateId } = conversationInfo;

                assistant = await createAssistant({
                    name,
                    assistantServiceId,
                    templateId,
                }).unwrap();
                await refetchAssistants();
            }

            const additionalAssistants =
                conversationInfo.additionalAssistantIds
                    ?.map((assistantId) => assistants?.find((a) => a.id === assistantId))
                    .filter((a) => a !== undefined) || [];

            if (conversationInfo.existingConversationId === undefined) {
                // send event to notify the conversation that the user has joined
                await createConversationMessage({
                    conversationId: conversation.id,
                    content: `${localUserName ?? 'Unknown user'} created the conversation`,
                    messageType: 'notice',
                });
            }

            for (const assistantAndMetadata of [
                { assistant, metadata: conversationInfo.participantMetadata },
                ...additionalAssistants.map((a) => ({ assistant: a, metadata: undefined })),
            ]) {
                // send notice message first, to announce before assistant reacts to create event
                await createConversationMessage({
                    conversationId: conversation.id,
                    content: `${assistantAndMetadata.assistant.name} added to conversation`,
                    messageType: 'notice',
                });

                await addConversationParticipant({
                    conversationId: conversation.id,
                    participantId: assistantAndMetadata.assistant.id,
                    metadata: assistantAndMetadata.metadata,
                });
            }

            return {
                assistant,
                conversation,
            };
        },
        [
            assistantsLoading,
            assistantServicesLoading,
            myAssistantServicesLoading,
            getConversation,
            createConversation,
            assistants,
            createAssistant,
            refetchAssistants,
            createConversationMessage,
            localUserName,
            addConversationParticipant,
        ],
    );

    const categorizedAssistantServices: Record<string, AssistantServiceTemplate[]> = React.useMemo(
        () => ({
            ...(assistantServices ?? [])
                .filter(
                    (service) =>
                        !myAssistantServices?.find(
                            (myService) => myService.assistantServiceId === service.assistantServiceId,
                        ),
                )
                .flatMap(
                    (service) =>
                        (service.templates ?? []).map((template) => ({
                            service,
                            template,
                        })) as AssistantServiceTemplate[],
                )
                .reduce((accumulated, assistantService) => {
                    const entry = Object.entries(Constants.assistantCategories).find(([_, serviceIds]) =>
                        serviceIds.includes(assistantService.service.assistantServiceId),
                    );
                    const assignedCategory = entry ? entry[0] : 'Other';
                    if (!accumulated[assignedCategory]) {
                        accumulated[assignedCategory] = [];
                    }
                    accumulated[assignedCategory].push(assistantService);
                    return accumulated;
                }, {} as Record<string, AssistantServiceTemplate[]>),
            'My Services': (myAssistantServices ?? []).flatMap(
                (service) =>
                    (service.templates ?? []).map((template) => ({
                        service,
                        template,
                    })) as AssistantServiceTemplate[],
            ),
        }),
        [assistantServices, myAssistantServices],
    );

    const orderedAssistantServicesCategories = React.useMemo(
        () =>
            [...Object.keys(Constants.assistantCategories), 'Other', 'My Services'].filter(
                (category) => categorizedAssistantServices[category]?.length,
            ),
        [categorizedAssistantServices],
    );

    const assistantServicesByCategories: { category: string; assistantServices: AssistantServiceTemplate[] }[] =
        React.useMemo(
            () =>
                orderedAssistantServicesCategories.map((category) => ({
                    category,
                    assistantServices:
                        categorizedAssistantServices[category]?.sort((a, b) =>
                            a.template.name.localeCompare(b.template.name),
                        ) ?? [],
                })),
            [categorizedAssistantServices, orderedAssistantServicesCategories],
        );

    return {
        isFetching,
        createConversation: create,
        assistantServicesByCategories,
        assistants,
    };
};
