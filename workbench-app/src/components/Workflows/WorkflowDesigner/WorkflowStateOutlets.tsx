// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
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
    Field,
    Input,
    Textarea,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    Add24Regular,
    ArrowDown24Regular,
    ArrowUp24Regular,
    ClipboardPasteRegular,
    Delete24Regular,
    PlugConnectedAddRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../../Constants';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CommandButton } from '../../App/CommandButton';
import { CopyButton } from '../../App/CopyButton';
import { LabelWithDescription } from '../../App/LabelWithDescription';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
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
        },
    },
    panel: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    field: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface WorkflowStateOutletsProps {
    workflowDefinition: WorkflowDefinition;
    stateIdToEdit: string;
    onChange: (newValue: WorkflowDefinition) => void;
}

export const WorkflowStateOutlets: React.FC<WorkflowStateOutletsProps> = (props) => {
    const { workflowDefinition, stateIdToEdit, onChange } = props;
    const classes = useClasses();
    const [pasteError, setPasteError] = React.useState<string>();

    const stateToEdit = workflowDefinition.states.find((state) => state.id === stateIdToEdit);
    if (!stateToEdit) {
        throw new Error(`State not found: ${stateIdToEdit}`);
    }

    const handleLabelChange = React.useCallback(
        (index: number, newValue: string) => {
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: state.outlets.map((outlet, outletIndex) => {
                                if (outletIndex === index) {
                                    return {
                                        ...outlet,
                                        label: newValue,
                                    };
                                }
                                return outlet;
                            }),
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateIdToEdit, workflowDefinition],
    );

    const handleEvaluateTransitionPromptChange = React.useCallback(
        (index: number, newValue: string) => {
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: state.outlets.map((outlet, outletIndex) => {
                                if (outletIndex === index) {
                                    return {
                                        ...outlet,
                                        prompts: {
                                            ...outlet.prompts,
                                            evaluateTransition: newValue,
                                        },
                                    };
                                }
                                return outlet;
                            }),
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateIdToEdit, workflowDefinition],
    );

    const handleContextTransferPromptChange = React.useCallback(
        (index: number, newValue: string) => {
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: state.outlets.map((outlet, outletIndex) => {
                                if (outletIndex === index) {
                                    return {
                                        ...outlet,
                                        prompts: {
                                            ...outlet.prompts,
                                            contextTransfer: newValue,
                                        },
                                    };
                                }
                                return outlet;
                            }),
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateIdToEdit, workflowDefinition],
    );

    const handleAddOutlet = React.useCallback(
        (addAfter?: number) => {
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: [
                                ...state.outlets.slice(0, addAfter !== undefined ? addAfter + 1 : state.outlets.length),
                                {
                                    id: generateUuid(),
                                    label: `Outlet ${stateToEdit.outlets.length + 1}`,
                                    prompts: {
                                        evaluateTransition: 'User has indicated they want to proceed to the next step.',
                                    },
                                },
                                ...state.outlets.slice(addAfter !== undefined ? addAfter + 1 : state.outlets.length),
                            ],
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateToEdit.outlets.length, stateIdToEdit, workflowDefinition],
    );

    const handleRemoveOutlet = React.useCallback(
        (removeAt: number) => {
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: state.outlets.filter((_outlet, index) => index !== removeAt),
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateIdToEdit, workflowDefinition],
    );

    const handleOrderChange = React.useCallback(
        (id: string, changeBy: number) => {
            const outlet = stateToEdit.outlets.find((outlet) => outlet.id === id);
            if (!outlet) {
                throw new Error(`Outlet not found: ${id}`);
            }

            const currentIndex = stateToEdit.outlets.indexOf(outlet);
            const newIndex = currentIndex + changeBy;

            if (newIndex < 0 || newIndex >= stateToEdit.outlets.length) {
                return;
            }

            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: state.outlets.map((outlet, index) => {
                                if (index === currentIndex) {
                                    return state.outlets[newIndex];
                                }
                                if (index === newIndex) {
                                    return state.outlets[currentIndex];
                                }
                                return outlet;
                            }),
                        };
                    }
                    return state;
                }),
            });
        },
        [onChange, stateToEdit.outlets, stateIdToEdit, workflowDefinition],
    );

    const handlePasteOutlet = React.useCallback(async () => {
        const clipboardErrorText = 'No valid outlet data found in the clipboard.';
        const clipboardData = await navigator.clipboard.readText();
        if (!clipboardData) {
            setPasteError(clipboardErrorText);
            return;
        }

        try {
            const outlet = JSON.parse(clipboardData);
            // ensure the outlet has a unique id
            outlet.id = generateUuid();

            handleAddOutlet();
            onChange({
                ...workflowDefinition,
                states: workflowDefinition.states.map((state) => {
                    if (state.id === stateIdToEdit) {
                        return {
                            ...state,
                            outlets: [...state.outlets, outlet],
                        };
                    }
                    return state;
                }),
            });
        } catch (error) {
            setPasteError(clipboardErrorText);
        }
    }, [handleAddOutlet, onChange, stateIdToEdit, workflowDefinition]);

    return (
        <div className={classes.root}>
            <div className={classes.row}>
                <Button
                    disabled={stateToEdit.outlets.length >= Constants.workflow.maxOutlets}
                    icon={<PlugConnectedAddRegular />}
                    onClick={() => handleAddOutlet()}
                >
                    Add Outlet
                </Button>
                <Tooltip content="Paste an outlet from the clipboard" relationship="description">
                    <Button icon={<ClipboardPasteRegular />} onClick={handlePasteOutlet} />
                </Tooltip>
                <Dialog open={!!pasteError} onOpenChange={() => setPasteError(undefined)}>
                    <DialogSurface>
                        <DialogBody>
                            <DialogTitle>Error Pasting Outlet</DialogTitle>
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
                {stateToEdit.outlets.map((outlet, index) => (
                    <AccordionItem key={index} value={outlet.id} className={classes.item}>
                        <Card className={classes.card}>
                            <AccordionHeader className={classes.header}>
                                <div
                                    className={classes.row}
                                    onClick={(event) => {
                                        // allow events to still flow to children, but not the accordion
                                        // so only stop propagation if the event is now in the bubble phase
                                        if (event.eventPhase === 3) {
                                            event.stopPropagation();
                                        }
                                    }}
                                >
                                    <Tooltip content="The label for this outlet" relationship="description">
                                        <Input
                                            onClick={(event) => event.stopPropagation()}
                                            placeholder="Label"
                                            value={outlet.label}
                                            onChange={(_event, data) => handleLabelChange(index, data.value)}
                                            aria-autocomplete="none"
                                        />
                                    </Tooltip>
                                    <Tooltip content="Move this outlet up" relationship="description">
                                        <Button
                                            as="a"
                                            disabled={index === 0}
                                            onClick={() => handleOrderChange(outlet.id, -1)}
                                            icon={<ArrowUp24Regular />}
                                        />
                                    </Tooltip>
                                    <Tooltip content="Move this outlet down" relationship="description">
                                        <Button
                                            as="a"
                                            disabled={index === stateToEdit.outlets.length - 1}
                                            onClick={() => handleOrderChange(outlet.id, 1)}
                                            icon={<ArrowDown24Regular />}
                                        />
                                    </Tooltip>
                                    <CommandButton
                                        as="a"
                                        icon={<Delete24Regular />}
                                        iconOnly
                                        description={
                                            'Remove this outlet from the state. If the outlet is connected to other states,' +
                                            ' the transitions will be removed as well.'
                                        }
                                        disabled={stateToEdit.outlets.length <= 1}
                                        dialogContent={{
                                            title: 'Remove Outlet',
                                            content: (
                                                <p>
                                                    Are you sure you want to remove <strong>{outlet.label}</strong>?
                                                </p>
                                            ),
                                            closeLabel: 'Cancel',
                                            additionalActions: [
                                                <Button
                                                    key="remove"
                                                    appearance="primary"
                                                    onClick={() => handleRemoveOutlet(index)}
                                                >
                                                    Remove
                                                </Button>,
                                            ],
                                        }}
                                    />
                                    <Tooltip content="Add a new outlet after this one" relationship="description">
                                        <Button
                                            as="a"
                                            disabled={stateToEdit.outlets.length >= Constants.workflow.maxOutlets}
                                            onClick={() => handleAddOutlet(index)}
                                            icon={<Add24Regular />}
                                        />
                                    </Tooltip>
                                    <CopyButton data={JSON.stringify(outlet)} tooltip="Copy this outlet" />
                                </div>
                            </AccordionHeader>
                            <AccordionPanel className={classes.panel}>
                                <Field
                                    label={
                                        <LabelWithDescription
                                            label="Evaluate Transition Criteria"
                                            description={[
                                                'The natural language criteria that will passed to evaluate',
                                                ' the recent chat history to determine if the transition should',
                                                ' be triggered. The evaluation result will be a true / false, so',
                                                ' for best results please consider writing the criteria accordingly.',
                                            ].join(' ')}
                                        />
                                    }
                                >
                                    <Textarea
                                        placeholder="Evaluate Transition Criteria"
                                        value={outlet.prompts.evaluateTransition}
                                        onChange={(_event, data) =>
                                            handleEvaluateTransitionPromptChange(index, data.value)
                                        }
                                    />
                                </Field>
                                <Field
                                    label={
                                        <LabelWithDescription
                                            label="Context Transfer Request"
                                            description={[
                                                'The natural language request to use with the conversation',
                                                ' history to transfer the context to the next state. The result will',
                                                " be inserted as a user message in the next state's conversation",
                                                ' history. This only applies if the next state uses a different',
                                                ' conversation.',
                                            ].join(' ')}
                                        />
                                    }
                                >
                                    <Textarea
                                        value={outlet.prompts.contextTransfer ?? ''}
                                        onChange={(_event, data) =>
                                            handleContextTransferPromptChange(index, data.value)
                                        }
                                    />
                                </Field>
                            </AccordionPanel>
                        </Card>
                    </AccordionItem>
                ))}
            </Accordion>
        </div>
    );
};
