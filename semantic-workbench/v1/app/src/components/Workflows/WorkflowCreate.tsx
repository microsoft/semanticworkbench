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
    Field,
    Input,
} from '@fluentui/react-components';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ConversationDefinition, WorkflowDefinition, WorkflowState } from '../../models/WorkflowDefinition';
import { useCreateWorkflowDefinitionMutation } from '../../services/workbench/workflow';

interface WorkflowCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (workflowDefinition: WorkflowDefinition) => void;
}

export const WorkflowCreate: React.FC<WorkflowCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const [createWorkflowDefinition] = useCreateWorkflowDefinitionMutation();
    const [label, setLabel] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);
    const workbenchService = useWorkbenchService();

    const handleSave = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        const rootConversationDefinition: ConversationDefinition = {
            id: generateUuid(),
            title: 'Main Conversation',
        };

        const initialState: WorkflowState = {
            id: generateUuid(),
            label: 'Start',
            conversationDefinitionId: rootConversationDefinition.id,
            assistantDataList: [],
            editorData: {
                position: { x: 0, y: 0 },
            },
            outlets: [
                {
                    id: generateUuid(),
                    label: 'Next Step',
                    prompts: {
                        evaluateTransition: 'User has indicated they want to proceed to the next step.',
                        contextTransfer: 'Summarize the recent conversation.',
                    },
                },
            ],
        };

        const defaults = await workbenchService.getWorkflowDefinitionDefaultsAsync();
        if (!defaults) {
            throw new Error('Failed to get workflow definition defaults');
        }

        const workflowDefinition = await createWorkflowDefinition({
            ...defaults,
            label,
            startStateId: initialState.id,
            states: [...defaults.states, initialState],
            definitions: {
                ...defaults.definitions,
                conversations: [...defaults.definitions.conversations, rootConversationDefinition],
            },
        }).unwrap();
        onOpenChange?.(false);
        onCreate?.(workflowDefinition);
    };

    React.useEffect(() => {
        if (!open) {
            return;
        }
        setLabel('');
        setSubmitted(false);
    }, [open]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>New Workflow</DialogTitle>
                    <DialogContent>
                        <form
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleSave();
                            }}
                        >
                            <Field label="Label">
                                <Input
                                    disabled={submitted}
                                    value={label}
                                    onChange={(_event, data) => setLabel(data.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                            <button disabled={submitted} type="submit" hidden />
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger disableButtonEnhancement>
                            <Button appearance="secondary">Cancel</Button>
                        </DialogTrigger>
                        <DialogTrigger>
                            <Button disabled={!label || submitted} appearance="primary" onClick={handleSave}>
                                {submitted ? 'Saving...' : 'Save'}
                            </Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
