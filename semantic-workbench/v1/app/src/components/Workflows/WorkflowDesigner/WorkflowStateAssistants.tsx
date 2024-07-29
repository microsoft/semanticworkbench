// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Button,
    Card,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Text,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { ClipboardPasteRegular, PlugDisconnected16Regular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantDefinition, WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CommandButton } from '../../App/CommandButton';
import { CopyButton } from '../../App/CopyButton';
import { AssistantDefinitionAdd } from './AssistantDefinitionAdd';
import { WorkflowStateAssistantEditor } from './WorkflowStateAssistantEditor';

const useClasses = makeStyles({
    item: {
        ...shorthands.margin(0, 0, tokens.spacingVerticalM, 0),
        '&:last-child': {
            marginBottom: 0,
        },
    },
    card: {
        ...shorthands.padding(tokens.spacingVerticalM, 0),
    },
    header: {
        '& > button': {
            minHeight: 'min-content',
            alignItems: 'start',
        },
    },
    panel: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    row: {
        display: 'flex',
        gap: tokens.spacingHorizontalXS,
        alignItems: 'center',
    },
});

interface WorkflowStateAssistantsProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

interface WorkflowStateAssistantExportData {
    assistantDefinition: AssistantDefinition;
    configData: any;
}

export const WorkflowStateAssistants: React.FC<WorkflowStateAssistantsProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange } = props;
    const classes = useClasses();
    const [pasteError, setPasteError] = React.useState<string | undefined>();

    const assistantDefinitions = workflowDefinition.definitions.assistants;
    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const handleRemoveAssistant = (assistantDefinitionId: string) => {
        onChange({
            ...workflowDefinition,
            states: workflowDefinition.states.map((state) => {
                if (state.id === stateIdToEdit) {
                    return {
                        ...state,
                        assistantDataList: state.assistantDataList?.filter(
                            (assistantData) => assistantData.assistantDefinitionId !== assistantDefinitionId,
                        ),
                    };
                }
                return state;
            }),
        });
    };

    const handlePasteAssistantDefinition = React.useCallback(async () => {
        const clipboardErrorText = 'No valid assistant definition data found in the clipboard.';
        const clipboardData = await navigator.clipboard.readText();
        if (!clipboardData) {
            setPasteError(clipboardErrorText);
            return;
        }

        try {
            const importData = JSON.parse(clipboardData) as WorkflowStateAssistantExportData;
            onChange({
                ...workflowDefinition,
                definitions: {
                    ...workflowDefinition.definitions,
                    assistants: [...workflowDefinition.definitions.assistants, importData.assistantDefinition],
                },
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            assistantDataList: [
                                ...(state.assistantDataList || []),
                                {
                                    assistantDefinitionId: importData.assistantDefinition.id,
                                    configData: importData.configData,
                                },
                            ],
                        };
                    }
                    return state;
                }),
            });
        } catch (error) {
            setPasteError(clipboardErrorText);
        }
    }, [onChange, workflowDefinition, stateIdToEdit]);

    return (
        <>
            <div className={classes.row}>
                <AssistantDefinitionAdd
                    workflowDefinition={workflowDefinition}
                    stateIdToEdit={stateIdToEdit}
                    onChange={onChange}
                />
                <Tooltip content="Paste an assistant definition from the clipboard" relationship="description">
                    <Button icon={<ClipboardPasteRegular />} onClick={handlePasteAssistantDefinition} />
                </Tooltip>
                <Dialog open={!!pasteError} onOpenChange={() => setPasteError(undefined)}>
                    <DialogSurface>
                        <DialogBody>
                            <DialogTitle>Error Pasting Assistant Definition</DialogTitle>
                            <DialogContent>
                                <p>{pasteError}</p>
                            </DialogContent>
                            <DialogActions>
                                <DialogTrigger disableButtonEnhancement>
                                    <Button appearance="secondary">Close</Button>
                                </DialogTrigger>
                            </DialogActions>
                        </DialogBody>
                    </DialogSurface>
                </Dialog>
            </div>
            <Accordion collapsible>
                {stateToEdit.assistantDataList?.map((assistantData) => {
                    const assistantDefinition = assistantDefinitions.find(
                        (a) => a.id === assistantData.assistantDefinitionId,
                    );
                    if (!assistantDefinition) {
                        throw new Error(`Assistant definition not found: ${assistantData.assistantDefinitionId}`);
                    }
                    const exportData: WorkflowStateAssistantExportData = {
                        assistantDefinition,
                        configData: assistantData.configData,
                    };
                    return (
                        <AccordionItem
                            value={assistantData.assistantDefinitionId}
                            key={assistantData.assistantDefinitionId}
                            className={classes.item}
                        >
                            <Card className={classes.card}>
                                <AccordionHeader className={classes.header}>
                                    <Text weight="semibold">{assistantDefinition.name}</Text>
                                </AccordionHeader>
                                <AccordionPanel className={classes.panel}>
                                    <div className={classes.row}>
                                        <CommandButton
                                            label="Remove Assistant"
                                            size="small"
                                            icon={<PlugDisconnected16Regular />}
                                            description="Remove this assistant from the state"
                                            dialogContent={{
                                                title: `Remove ${assistantDefinition.name}`,
                                                content: `Are you sure you want to remove "${assistantDefinition.name}" from the current state? Any config overrides will be lost.`,
                                                closeLabel: 'Cancel',
                                                additionalActions: [
                                                    <Button
                                                        key="remove"
                                                        appearance="primary"
                                                        onClick={() =>
                                                            handleRemoveAssistant(assistantData.assistantDefinitionId)
                                                        }
                                                    >
                                                        Remove Assistant
                                                    </Button>,
                                                ],
                                            }}
                                        />
                                        <CopyButton
                                            key="copy"
                                            size="small"
                                            tooltip="Copy the assistant data to the clipboard as JSON. This can be useful for debugging or pasting into a new assistant."
                                            data={JSON.stringify(exportData, null, 2)}
                                        />
                                    </div>
                                    <WorkflowStateAssistantEditor
                                        workflowDefinition={workflowDefinition}
                                        stateIdToEdit={stateIdToEdit}
                                        assistantIdToEdit={assistantData.assistantDefinitionId}
                                        onChange={onChange}
                                    />
                                </AccordionPanel>
                            </Card>
                        </AccordionItem>
                    );
                })}
            </Accordion>
        </>
    );
};
