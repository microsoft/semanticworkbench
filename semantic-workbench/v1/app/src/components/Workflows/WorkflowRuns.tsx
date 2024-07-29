// Copyright (c) Microsoft. All rights reserved.

import { Play20Regular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowRun } from '../../models/WorkflowRun';
import { useGetWorkflowRunsQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { WorkflowRunCreate } from './WorkflowRunCreate';
import { WorkflowRunRemove } from './WorkflowRunRemove';

interface WorkflowRunsProps {
    workflowDefinitionId: string;
    workflowRuns?: WorkflowRun[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (workflowRun: WorkflowRun) => void;
}

export const WorkflowRuns: React.FC<WorkflowRunsProps> = (props) => {
    const { workflowDefinitionId, workflowRuns, title, hideInstruction, onCreate } = props;
    const { refetch: refetchWorkflowRuns } = useGetWorkflowRunsQuery();
    const [showCreateOpen, setShowCreateOpen] = React.useState(false);

    const handleWorkflowRunCreate = async (workflowRun: WorkflowRun) => {
        await refetchWorkflowRuns();
        onCreate?.(workflowRun);
    };

    return (
        <MyItemsManager
            items={workflowRuns?.map((workflowRun) => (
                <MiniControl
                    key={workflowRun.id}
                    icon={<Play20Regular />}
                    label={workflowRun.title}
                    linkUrl={`/workflow/${encodeURIComponent(workflowDefinitionId)}/run/${encodeURIComponent(
                        workflowRun.id,
                    )}`}
                    actions={
                        <>
                            <WorkflowRunRemove workflowRun={workflowRun} iconOnly />
                        </>
                    }
                />
            ))}
            title={title ?? 'Workflow Runs'}
            itemLabel="Workflow Run"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Play20Regular />}
                        label={`New Workflow Run`}
                        description={`Create a new workflow run`}
                        onClick={() => setShowCreateOpen(true)}
                    />
                    <WorkflowRunCreate
                        workflowDefinitionId={workflowDefinitionId}
                        open={showCreateOpen}
                        onOpenChange={(open) => setShowCreateOpen(open)}
                        onCreate={handleWorkflowRunCreate}
                    />
                </>
            }
        />
    );
};
