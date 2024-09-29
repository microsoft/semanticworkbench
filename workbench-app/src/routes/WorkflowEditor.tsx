// Copyright (c) Microsoft. All rights reserved.

import { Title3, makeStyles, tokens } from '@fluentui/react-components';
import { PlayRegular, SettingsRegular } from '@fluentui/react-icons';
import React from 'react';
import { useParams } from 'react-router-dom';
import { ReactFlowProvider } from 'reactflow';
import 'reactflow/dist/style.css';
import { AppView } from '../components/App/AppView';
import { CommandButton } from '../components/App/CommandButton';
import { Loading } from '../components/App/Loading';
import { WorkflowDesigner } from '../components/Workflows/WorkflowDesigner/WorkflowDesigner';
import { useGetWorkflowDefinitionQuery } from '../services/workbench/workflow';

const useClasses = makeStyles({
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
    },
});

export const WorkflowEditor: React.FC = () => {
    const { workflowDefinitionId } = useParams();
    const classes = useClasses();
    const [showSettings, setShowSettings] = React.useState(false);

    if (!workflowDefinitionId) {
        throw new Error('Workflow Definition ID is required');
    }
    const {
        data: workflowDefinition,
        error: workflowDefinitionError,
        isLoading: isLoadingWorkflowDefinition,
    } = useGetWorkflowDefinitionQuery(workflowDefinitionId);

    if (workflowDefinitionError) {
        const errorMessage = JSON.stringify(workflowDefinitionError);
        throw new Error(`Error loading workflow definition: ${errorMessage}`);
    }

    if (isLoadingWorkflowDefinition) {
        return (
            <AppView title="Edit Workflow">
                <Loading />
            </AppView>
        );
    }

    if (!workflowDefinition) {
        throw new Error('Workflow definition not found');
    }

    const actions = {
        items: [
            <CommandButton
                key="workflow-runner"
                icon={<PlayRegular />}
                iconOnly
                label="Workflow Runner"
                onClick={() => {
                    window.location.href = `/workflow/${workflowDefinitionId}`;
                }}
            />,
        ],
    };

    const title = (
        <div className={classes.row}>
            <CommandButton
                key="workflow-settings"
                icon={<SettingsRegular />}
                iconOnly
                label="Settings"
                onClick={() => setShowSettings(true)}
            />
            <Title3 className={classes.title}>{workflowDefinition.label}</Title3>
        </div>
    );

    return (
        <AppView title={title} actions={actions} fullSizeContent>
            <ReactFlowProvider>
                <WorkflowDesigner
                    workflowDefinition={workflowDefinition}
                    showSettings={showSettings}
                    onShowSettingsChange={(value) => setShowSettings(value)}
                />
            </ReactFlowProvider>
        </AppView>
    );
};
