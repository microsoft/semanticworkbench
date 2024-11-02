import {
    Button,
    Checkbox,
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
import { Info16Regular, PresenceAvailableRegular, PresenceOfflineRegular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
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

export const useCreateConversationControls = () => {
    const classes = useClasses();
    const { create: createConversation, assistants, assistantServicesByCategories } = useCreateConversation();

    const [title, setTitle] = React.useState('');
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');
    const [manualEntry, setManualEntry] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();

    const preventSubmit =
        submitted || !title || !assistantId || (assistantId === 'new' && (!assistantServiceId || !name));

    const handleCreate = async () => {
        if (preventSubmit) {
            return;
        }
        setSubmitted(true);

        const assistantInfo = { assistantId, name, assistantServiceId };

        try {
            const { conversation } = await createConversation(title, assistantInfo);
            navigateToConversation(conversation.id);
        } finally {
            // In case of error, allow user to retry
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
                {assistants
                    ?.sort((a, b) => a.name.localeCompare(b.name))
                    .map((assistant) => (
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

    const assistantServicesOptions = assistantServicesByCategories.map(({ category, assistantServices }) => (
        <OptionGroup key={category} label={category}>
            {assistantServices
                .sort((a, b) => a.name.localeCompare(b.name))
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

    const createConversationForm = () => (
        <form
            onSubmit={(event) => {
                event.preventDefault();
                handleCreate();
            }}
        >
            <div className={classes.content}>
                <Field label="Title">
                    <Input
                        disabled={submitted}
                        value={title}
                        onChange={(_event, data) => setTitle(data?.value)}
                        aria-autocomplete="none"
                    />
                </Field>
                <Field label="Assistant">
                    <Dropdown
                        placeholder="Select an assistant"
                        disabled={submitted}
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
                                    disabled={submitted}
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
                                    disabled={submitted}
                                    value={assistantServiceId}
                                    onChange={(_event, data) => setAssistantServiceId(data?.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                        )}
                        <Field label="Name">
                            <Input
                                disabled={submitted}
                                value={name}
                                onChange={(_event, data) => setName(data?.value)}
                                aria-autocomplete="none"
                            />
                        </Field>
                        <div className={classes.serviceOptions}>
                            <Checkbox
                                disabled={submitted}
                                style={{ whiteSpace: 'nowrap' }}
                                label="Enter Assistant Service ID"
                                checked={manualEntry}
                                onChange={(_event, data) => setManualEntry(data.checked === true)}
                            />
                            <AssistantImport label="Import Assistant" disabled={submitted} />
                        </div>
                    </>
                )}
                <button disabled={preventSubmit} type="submit" hidden />
            </div>
        </form>
    );

    const createConversationSubmitButton = () => (
        <Button appearance="primary" onClick={handleCreate} disabled={preventSubmit}>
            New Conversation
        </Button>
    );

    return {
        createConversationForm,
        createConversationSubmitButton,
    };
};
