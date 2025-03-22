// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Checkbox,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Divider,
    Dropdown,
    Field,
    Input,
    Label,
    Option,
    OptionGroup,
    Tooltip,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { Info16Regular, PresenceAvailableRegular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../Constants';
import { Assistant } from '../../models/Assistant';
import { AssistantServiceInfo } from '../../models/AssistantServiceInfo';
import {
    useCreateAssistantMutation,
    useGetAssistantServiceInfosQuery,
    useGetAssistantsQuery,
} from '../../services/workbench';
import { AssistantImport } from './AssistantImport';

const useClasses = makeStyles({
    dialogContent: {
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
});

interface AssistantCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (assistant: Assistant) => void;
    onImport?: (result: { assistantIds: string[]; conversationIds: string[] }) => void;
}

export const AssistantCreate: React.FC<AssistantCreateProps> = (props) => {
    const { open, onOpenChange, onCreate, onImport } = props;
    const classes = useClasses();
    const { refetch: refetchAssistants } = useGetAssistantsQuery();
    const {
        data: assistantServices,
        refetch: refetchAssistantServices,
        error: getAssistantServicesError,
        isLoading: isLoadingAssistantServices,
    } = useGetAssistantServiceInfosQuery({});
    const {
        data: myAssistantServices,
        refetch: refetchMyAssistantServices,
        error: getMyAssistantServicesError,
        isLoading: isLoadingMyAssistantServices,
    } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });
    const [createAssistant] = useCreateAssistantMutation();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');
    const [templateId, setTemplateId] = React.useState('');
    const [manualEntry, setManualEntry] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);

    if (getAssistantServicesError) {
        const errorMessage = JSON.stringify(getAssistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }
    if (getMyAssistantServicesError) {
        const errorMessage = JSON.stringify(getMyAssistantServicesError);
        throw new Error(`Error loading my assistant services: ${errorMessage}`);
    }

    const handleSave = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const assistant = await createAssistant({
                name,
                assistantServiceId,
                templateId: templateId,
            }).unwrap();
            await refetchAssistants();
            onOpenChange?.(false);
            onCreate?.(assistant);
        } finally {
            setSubmitted(false);
        }
    };

    React.useEffect(() => {
        if (!open) {
            return;
        }

        refetchAssistantServices();
        refetchMyAssistantServices();
        setName('');
        setAssistantServiceId('');
        setManualEntry(false);
        setSubmitted(false);
    }, [open, refetchAssistantServices, refetchMyAssistantServices]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    const handleImport = async (result: { assistantIds: string[]; conversationIds: string[] }) => {
        // actual import already handled inside the AssistantImport component
        onOpenChange?.(false);
        onImport?.(result);
    };

    const handleImportError = () => {
        onOpenChange?.(false);
    };

    const categorizedAssistantServices: Record<string, AssistantServiceInfo[]> = {
        ...(assistantServices ?? [])
            .filter(
                (service) =>
                    !myAssistantServices?.find(
                        (myService) => myService.assistantServiceId === service.assistantServiceId,
                    ),
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
            }, {} as Record<string, AssistantServiceInfo[]>),
        'My Services': myAssistantServices ?? [],
    };

    const orderedCategories = [...Object.keys(Constants.assistantCategories), 'Other', 'My Services'].filter(
        (category) => categorizedAssistantServices[category]?.length,
    );

    const options = orderedCategories.map((category) => (
        <OptionGroup key={category} label={category}>
            {(categorizedAssistantServices[category] ?? [])
                .flatMap((assistantService) => {
                    return assistantService.templates.map((template) => ({
                        assistantServiceId: assistantService.assistantServiceId,
                        name: template.name,
                        templateId: template.id,
                        description: template.description,
                    }));
                })
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((assistantService) => {
                    const key = JSON.stringify([assistantService.assistantServiceId, assistantService.templateId]);
                    return (
                        <Option key={key} text={assistantService.name} value={key}>
                            <div className={classes.option}>
                                <PresenceAvailableRegular color="green" />
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
                                            <Label size="small">Assistant type ID:</Label>
                                            <Label size="small">{assistantService.templateId}</Label>
                                        </div>
                                    }
                                    relationship="description"
                                >
                                    <Info16Regular />
                                </Tooltip>
                            </div>
                        </Option>
                    );
                })}
        </OptionGroup>
    ));

    if (isLoadingAssistantServices || isLoadingMyAssistantServices) {
        return null;
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <DialogBody>
                        <DialogTitle>New Assistant</DialogTitle>
                        <DialogContent className={classes.dialogContent}>
                            {!manualEntry && (
                                <Field label="Assistant Service">
                                    <Dropdown
                                        placeholder="Select an assistant service"
                                        disabled={submitted}
                                        onOptionSelect={(_event, data) => {
                                            if (data.optionValue) {
                                                const [assistantServiceId, templateId] = JSON.parse(data.optionValue);
                                                setAssistantServiceId(assistantServiceId);
                                                setTemplateId(templateId);
                                            }

                                            if (data.optionText && name === '') {
                                                setName(data.optionText);
                                            }
                                        }}
                                    >
                                        {options}
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
                            <button disabled={!name || !assistantServiceId || submitted} type="submit" hidden />
                        </DialogContent>
                        <DialogActions>
                            <Checkbox
                                style={{ whiteSpace: 'nowrap' }}
                                label="Enter Assistant Service ID"
                                checked={manualEntry}
                                onChange={(_event, data) => setManualEntry(data.checked === true)}
                            />
                            <AssistantImport disabled={submitted} onImport={handleImport} onError={handleImportError} />
                            <DialogTrigger disableButtonEnhancement>
                                <Button appearance="secondary">Cancel</Button>
                            </DialogTrigger>
                            <DialogTrigger disableButtonEnhancement>
                                <Button
                                    disabled={!name || !assistantServiceId || submitted}
                                    appearance="primary"
                                    onClick={handleSave}
                                >
                                    {submitted ? 'Saving...' : 'Save'}
                                </Button>
                            </DialogTrigger>
                        </DialogActions>
                    </DialogBody>
                </form>
            </DialogSurface>
        </Dialog>
    );
};
