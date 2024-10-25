import {
    Button,
    Checkbox,
    DialogTrigger,
    Divider,
    Dropdown,
    Field,
    Input,
    Label,
    makeStyles,
    Option,
    OptionGroup,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import { ChatAddRegular, Info16Regular, PresenceAvailableRegular, PresenceOfflineRegular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../../Constants';
import { Assistant } from '../../../models/Assistant';
import { AssistantServiceRegistration } from '../../../models/AssistantServiceRegistration';
import { useAppDispatch } from '../../../redux/app/hooks';
import { setActiveConversationId } from '../../../redux/features/app/appSlice';
import {
    useAddConversationParticipantMutation,
    useCreateAssistantMutation,
    useCreateConversationMessageMutation,
    useCreateConversationMutation,
    useGetAssistantServiceRegistrationsQuery,
    useGetAssistantsQuery,
} from '../../../services/workbench';
import { CommandButton } from '../../App/CommandButton';
import { AssistantImport } from '../../Assistants/AssistantImport';

const useClasses = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    option: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalXS,
    },
    optionDescription: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXS,
    },
    serviceOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
});

export const NewConversationButton: React.FC = () => {
    const classes = useClasses();
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

    const [createAssistant] = useCreateAssistantMutation();
    const [createConversation] = useCreateConversationMutation();
    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const [title, setTitle] = React.useState('');
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');
    const [manualEntry, setManualEntry] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);
    const dispatch = useAppDispatch();

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

    if (assistantsLoading || assistantServicesLoading || myAssistantServicesLoading) {
        return null;
    }

    const handleCreate = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        let assistant: Assistant | undefined = undefined;

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

        try {
            const conversation = await createConversation({ title }).unwrap();

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

            dispatch(setActiveConversationId(conversation.id));
        } finally {
            setSubmitted(false);
        }

        // Reset form
        setTitle('');
        setAssistantId(undefined);
        setName('');
        setAssistantServiceId('');
        setManualEntry(false);
    };

    const assistantOptions = (
        <>
            <OptionGroup label="Existing Assistants">
                {assistants?.map((assistant) => (
                    <Option key={assistant.id} text={assistant.name} value={assistant.id}>
                        {assistant.name}
                    </Option>
                ))}
            </OptionGroup>
            <OptionGroup label="New Assistant">
                <Option text="Create new assistant" value="new">
                    Create new assistant
                </Option>
            </OptionGroup>
        </>
    );

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

    const assistantServicesOptions = orderedAssistantServicesCategories.map((category) => (
        <OptionGroup key={category} label={category}>
            {(categorizedAssistantServices[category] ?? [])
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistantService) => (
                    <Option
                        key={assistantService.assistantServiceId}
                        text={assistantService.name}
                        value={assistantService.assistantServiceId}
                    >
                        <div className={classes.option}>
                            {assistantService.assistantServiceOnline ? (
                                <PresenceAvailableRegular color="green" />
                            ) : (
                                <PresenceOfflineRegular color="red" />
                            )}
                            <Label weight="semibold">{assistantService.name}</Label>
                            <Tooltip
                                content={
                                    <div className={classes.optionDescription}>
                                        <Label size="small">
                                            <em>{assistantService.description}</em>
                                        </Label>
                                        <Divider />
                                        <Label size="small">Assistant service ID:</Label>
                                        <Label size="small">{assistantService.assistantServiceId}</Label>
                                        <Divider />
                                        <Label size="small">Hosted at:</Label>
                                        <Label size="small">{assistantService.assistantServiceUrl}</Label>
                                        <Divider />
                                        <Label size="small">Created by:</Label>
                                        <Label size="small">{assistantService.createdByUserName}</Label>
                                        <Label size="small">[{assistantService.createdByUserId}]</Label>
                                    </div>
                                }
                                relationship="description"
                            >
                                <Info16Regular />
                            </Tooltip>
                        </div>
                    </Option>
                ))}
        </OptionGroup>
    ));

    const disabled = submitted || !title || !assistantId || (assistantId === 'new' && (!assistantServiceId || !name));

    return (
        <CommandButton
            description="New Conversation with Assistant"
            icon={<ChatAddRegular />}
            iconOnly
            dialogContent={{
                title: 'New Conversation',
                content: (
                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            handleCreate();
                        }}
                    >
                        <div className={classes.content}>
                            <Field label="Title">
                                <Input
                                    disabled={disabled}
                                    value={title}
                                    onChange={(_event, data) => setTitle(data?.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                            <Field label="Assistant">
                                <Dropdown
                                    placeholder="Select an assistant"
                                    disabled={disabled}
                                    onOptionSelect={(_event, data) => setAssistantId(data.optionValue)}
                                >
                                    {assistantOptions}
                                </Dropdown>
                            </Field>
                            {assistantId === 'new' && (
                                <>
                                    {!manualEntry && (
                                        <Field label="Assistant Service">
                                            <Dropdown
                                                placeholder="Select an assistant service"
                                                disabled={disabled}
                                                onOptionSelect={(_event, data) => {
                                                    if (data.optionValue) {
                                                        setAssistantServiceId(data.optionValue as string);
                                                    }

                                                    if (data.optionText && name === '') {
                                                        setName(data.optionText);
                                                    }
                                                }}
                                            >
                                                {assistantServicesOptions}
                                            </Dropdown>
                                        </Field>
                                    )}
                                    {manualEntry && (
                                        <Field label="Assistant Service ID">
                                            <Input
                                                disabled={disabled}
                                                value={assistantServiceId}
                                                onChange={(_event, data) => setAssistantServiceId(data?.value)}
                                                aria-autocomplete="none"
                                            />
                                        </Field>
                                    )}
                                    <Field label="Name">
                                        <Input
                                            disabled={disabled}
                                            value={name}
                                            onChange={(_event, data) => setName(data?.value)}
                                            aria-autocomplete="none"
                                        />
                                    </Field>
                                    <div className={classes.serviceOptions}>
                                        <Checkbox
                                            style={{ whiteSpace: 'nowrap' }}
                                            label="Enter Assistant Service ID"
                                            checked={manualEntry}
                                            onChange={(_event, data) => setManualEntry(data.checked === true)}
                                        />
                                        <AssistantImport label="Import Assistant" disabled={disabled} />
                                    </div>
                                </>
                            )}
                            <button disabled={disabled} type="submit" hidden />
                        </div>
                    </form>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="create">
                        <Button appearance="primary" onClick={handleCreate} disabled={disabled}>
                            New Conversation
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
