// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import {
    Button,
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
import { Info16Regular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../../Constants';
import { AssistantServiceRegistration } from '../../../models/AssistantServiceRegistration';
import { AssistantDefinition } from '../../../models/WorkflowDefinition';
import { useGetAssistantServiceRegistrationsQuery } from '../../../services/workbench';

const useClasses = makeStyles({
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
    onCreate?: (assistantDefinition: AssistantDefinition) => void;
}

export const AssistantDefinitionCreate: React.FC<AssistantCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const classes = useClasses();
    const [name, setName] = React.useState('');
    const [assistantServiceId, setAssistantServiceId] = React.useState('');

    const {
        data: assistantServices,
        error: getAssistantServicesError,
        isLoading: isLoadingAssistantServices,
    } = useGetAssistantServiceRegistrationsQuery({});

    if (getAssistantServicesError) {
        const errorMessage = JSON.stringify(getAssistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }

    const handleSave = async () => {
        onOpenChange?.(false);
        onCreate?.({
            id: generateUuid(),
            name,
            assistantServiceId,
        });
    };

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    const orderedCategories = Object.keys(Constants.assistantCategories);

    const categorizedAssistantServices = (assistantServices ?? []).reduce((acc, assistantService) => {
        let assignedCategory = 'Other';
        for (const [category, serviceIds] of Object.entries(Constants.assistantCategories)) {
            if (!serviceIds.includes(assistantService.assistantServiceId)) {
                continue;
            }
            assignedCategory = category;
            break;
        }
        if (!acc[assignedCategory]) {
            acc[assignedCategory] = [];
        }
        acc[assignedCategory].push(assistantService);
        return acc;
    }, {} as Record<string, AssistantServiceRegistration[]>);

    for (const category of Object.keys(categorizedAssistantServices)) {
        if (!orderedCategories.includes(category)) {
            orderedCategories.push(category);
        }
    }

    const options = orderedCategories.map((category) => (
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
                            <Label weight="semibold">{assistantService.name}</Label>
                            <Tooltip
                                content={
                                    <div className={classes.optionDescription}>
                                        <Label size="small">
                                            <em>{assistantService.description}</em>
                                        </Label>
                                        <Divider />
                                        <Label size="small">{assistantService.assistantServiceUrl}</Label>
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

    if (isLoadingAssistantServices) {
        return null;
    }

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>New Assistant</DialogTitle>
                    <DialogContent>
                        <form
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleSave();
                                return true;
                            }}
                        >
                            <Field label="Name">
                                <Input
                                    value={name}
                                    onChange={(_event, data) => setName(data?.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                            <Field label="Assistant Service">
                                <Dropdown
                                    placeholder="Select an assistant service"
                                    onOptionSelect={(_event, data) =>
                                        data.optionValue && setAssistantServiceId(data.optionValue as string)
                                    }
                                >
                                    {options}
                                </Dropdown>
                            </Field>
                            <button type="submit" hidden disabled={!name || !assistantServiceId} />
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Cancel</Button>
                        </DialogTrigger>
                        <DialogTrigger>
                            <Button appearance="primary" onClick={handleSave} disabled={!name || !assistantServiceId}>
                                Save
                            </Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
