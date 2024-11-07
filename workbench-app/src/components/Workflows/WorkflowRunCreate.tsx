// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { WorkflowRun } from '../../models/WorkflowRun';
import { useCreateWorkflowRunMutation, useGetWorkflowRunsQuery } from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface WorkflowRunCreateProps {
    workflowDefinitionId: string;
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (workflowRun: WorkflowRun) => void;
}

export const WorkflowRunCreate: React.FC<WorkflowRunCreateProps> = (props) => {
    const { workflowDefinitionId, open, onOpenChange, onCreate } = props;
    const classes = useClasses();
    const { refetch: refetchWorkflowRuns } = useGetWorkflowRunsQuery(workflowDefinitionId);
    const [createWorkflowRun] = useCreateWorkflowRunMutation();
    const [title, setTitle] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    const handleSave = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const workflowRun = await createWorkflowRun({
                title,
                workflowDefinitionId,
            }).unwrap();

            await refetchWorkflowRuns();
            onOpenChange?.(false);
            onCreate?.(workflowRun);
        } finally {
            setSubmitted(false);
        }
    }, [createWorkflowRun, onCreate, onOpenChange, refetchWorkflowRuns, submitted, title, workflowDefinitionId]);

    React.useEffect(() => {
        if (!open) {
            return;
        }

        setTitle('');
        setSubmitted(false);
    }, [open]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={handleOpenChange}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            title="New Run of Workflow"
            content={
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <Field label="Title of Run">
                        <Input
                            disabled={submitted}
                            value={title}
                            onChange={(_event, data) => setTitle(data?.value)}
                            aria-autocomplete="none"
                        />
                    </Field>
                </form>
            }
            closeLabel="Cancel"
            additionalActions={[
                <DialogTrigger key="save" disableButtonEnhancement>
                    <Button disabled={!title || submitted} appearance="primary" onClick={handleSave}>
                        {submitted ? 'Saving...' : 'Save'}
                    </Button>
                </DialogTrigger>,
            ]}
        />
    );
};
