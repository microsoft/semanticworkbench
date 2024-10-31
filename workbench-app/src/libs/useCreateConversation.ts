import { useAccount } from '@azure/msal-react';
import React from 'react';
import { Constants } from '../Constants';
import { Assistant } from '../models/Assistant';
import { AssistantServiceRegistration } from '../models/AssistantServiceRegistration';
import {
    useAddConversationParticipantMutation,
    useCreateAssistantMutation,
    useCreateConversationMessageMutation,
    useCreateConversationMutation,
    useGetAssistantServiceRegistrationsQuery,
    useGetAssistantsQuery,
} from '../services/workbench';

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
    } = useGetAssistantServiceRegistrationsQuery({});
    const {
        data: myAssistantServices,
        error: myAssistantServicesError,
        isLoading: myAssistantServicesLoading,
    } = useGetAssistantServiceRegistrationsQuery({ userIds: ['me'] });

    const account = useAccount();
    const [createAssistant] = useCreateAssistantMutation();
    const [createConversation] = useCreateConversationMutation();
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [isFetching, setIsFetching] = React.useState(false);

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

    const create = async (
        title: string,
        assistantInfo?: {
            assistantId: string;
            name: string;
            assistantServiceId: string;
        },
    ) => {
        if (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading) {
            throw new Error('Cannot create conversation while loading assistants or assistant services');
        }

        let assistant: Assistant | undefined = undefined;

        const conversation = await createConversation({ title }).unwrap();

        if (assistantInfo) {
            const { assistantId, name, assistantServiceId } = assistantInfo;

            if (assistantId === 'new') {
                assistant = await createAssistant({
                    name,
                    assistantServiceId,
                }).unwrap();
                await refetchAssistants();
            } else {
                assistant = assistants?.find((a) => a.id === assistantId);
            }

            if (!assistant) {
                throw new Error('Assistant not found');
            }

            // send event to notify the conversation that the user has joined
            const accountName = account?.name;
            if (accountName) {
                await createConversationMessage({
                    conversationId: conversation.id,
                    content: `${accountName} created the conversation`,
                    messageType: 'notice',
                });
            }

            // send notice message first, to announce before assistant reacts to create event
            await createConversationMessage({
                conversationId: conversation.id,
                content: `${assistant.name} added to conversation`,
                messageType: 'notice',
            });

            await addConversationParticipant({
                conversationId: conversation.id,
                participantId: assistant.id,
            });
        }

        return {
            assistant,
            conversation,
        };
    };

    const categorizedAssistantServices: Record<string, AssistantServiceRegistration[]> = {
        ...(assistantServices ?? [])
            .filter(
                (service) =>
                    !myAssistantServices?.find(
                        (myService) => myService.assistantServiceId === service.assistantServiceId,
                    ) && service.assistantServiceUrl !== null,
            )
            .reduce((accumulated, assistantService) => {
                const entry = Object.entries(Constants.assistantCategories).find(([_, serviceIds]) =>
                    serviceIds.includes(assistantService.assistantServiceId),
                );
                const assignedCategory = entry ? entry[0] : 'Other';
                if (!accumulated[assignedCategory]) {
                    accumulated[assignedCategory] = [];
                }
                accumulated[assignedCategory].push(assistantService);
                return accumulated;
            }, {} as Record<string, AssistantServiceRegistration[]>),
        'My Services': myAssistantServices?.filter((service) => service.assistantServiceUrl !== null) ?? [],
    };

    const orderedAssistantServicesCategories = [
        ...Object.keys(Constants.assistantCategories),
        'Other',
        'My Services',
    ].filter((category) => categorizedAssistantServices[category]?.length);

    const assistantServicesByCategories: { category: string; assistantServices: AssistantServiceRegistration[] }[] =
        orderedAssistantServicesCategories.map((category) => ({
            category,
            assistantServices:
                categorizedAssistantServices[category]?.sort((a, b) => a.name.localeCompare(b.name)) ?? [],
        }));

    return {
        isFetching,
        create,
        assistantServicesByCategories,
        assistants,
    };
};
