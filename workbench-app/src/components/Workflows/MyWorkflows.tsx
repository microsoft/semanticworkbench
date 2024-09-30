// Copyright (c) Microsoft. All rights reserved.

import { Button } from '@fluentui/react-components';
import { EditRegular, Flowchart24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { WorkflowDefinition } from '../../models/WorkflowDefinition';
import { useGetWorkflowDefinitionsQuery } from '../../services/workbench/workflow';
import { CommandButton } from '../App/CommandButton';
import { MiniControl } from '../App/MiniControl';
import { MyItemsManager } from '../App/MyItemsManager';
import { WorkflowCreate } from './WorkflowCreate';
import { WorkflowRemove } from './WorkflowRemove';

interface MyWorkflowsProps {
    workflowDefinitions?: WorkflowDefinition[];
    title?: string;
    hideInstruction?: boolean;
    onCreate?: (workflow: WorkflowDefinition) => void;
}

export const MyWorkflows: React.FC<MyWorkflowsProps> = (props) => {
    const { workflowDefinitions, title, hideInstruction, onCreate } = props;
    const { refetch: refetchWorkflowDefinitions } = useGetWorkflowDefinitionsQuery();
    const [workflowCreateOpen, setWorkflowCreateOpen] = React.useState(false);

    const handleWorkflowDefinitionCreate = async (workflowDefinition: WorkflowDefinition) => {
        await refetchWorkflowDefinitions();
        onCreate?.(workflowDefinition);
    };

    return (
        <MyItemsManager
            items={workflowDefinitions
                ?.toSorted((a, b) => a.label.localeCompare(b.label))
                .map((workflow) => (
                    <MiniControl
                        key={workflow.id}
                        icon={<Flowchart24Regular />}
                        label={workflow.label}
                        linkUrl={`/workflow/${encodeURIComponent(workflow.id)}`}
                        actions={
                            <>
                                <Link to={`/workflow/${workflow.id}/edit`}>
                                    <Button icon={<EditRegular />} />
                                </Link>
                                <WorkflowRemove workflowDefinition={workflow} iconOnly />
                            </>
                        }
                    />
                ))}
            title={title ?? 'My Workflows'}
            itemLabel="Workflow"
            hideInstruction={hideInstruction}
            actions={
                <>
                    <CommandButton
                        icon={<Flowchart24Regular />}
                        label={`New Workflow`}
                        description={`Create a new workflow`}
                        onClick={() => setWorkflowCreateOpen(true)}
                    />
                    <WorkflowCreate
                        open={workflowCreateOpen}
                        onOpenChange={(open) => setWorkflowCreateOpen(open)}
                        onCreate={handleWorkflowDefinitionCreate}
                    />
                </>
            }
        />
    );
};
