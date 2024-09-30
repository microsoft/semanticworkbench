// Copyright (c) Microsoft. All rights reserved.

import { Title3, Toolbar, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { WorkflowEdit } from '../components/Workflows/WorkflowEdit';
import { WorkflowRemove } from '../components/Workflows/WorkflowRemove';
import { WorkflowRuns } from '../components/Workflows/WorkflowRuns';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useGetWorkflowDefinitionQuery, useGetWorkflowRunsQuery } from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateRows: '1fr auto',
        height: '100%',
        gap: tokens.spacingVerticalM,
    },
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    title: {
        color: tokens.colorNeutralForegroundOnBrand,
    },
    content: {
        overflowY: 'auto',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
    toolbar: {
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        borderRadius: tokens.borderRadiusMedium,
    },
});

export const WorkflowRunEditor: React.FC = () => {
    const { workflowDefinitionId } = useParams();
    if (!workflowDefinitionId) {
        throw new Error('Workflow Definition ID is required');
    }
    const classes = useClasses();
    const {
        data: workflowDefinition,
        error: workflowDefinitionError,
        isLoading: isLoadingWorkflowDefinition,
    } = useGetWorkflowDefinitionQuery(workflowDefinitionId);
    const {
        data: workflowRuns,
        error: workflowRunsError,
        isLoading: isLoadingWorkflowRuns,
    } = useGetWorkflowRunsQuery(workflowDefinitionId);

    if (workflowDefinitionError) {
        const errorMessage = JSON.stringify(workflowDefinitionError);
        throw new Error(`Error loading workflow definition: ${errorMessage}`);
    }

    if (workflowRunsError) {
        const errorMessage = JSON.stringify(workflowRunsError);
        throw new Error(`Error loading workflow runs: ${errorMessage}`);
    }

    const siteUtility = useSiteUtility();

    React.useEffect(() => {
        if (isLoadingWorkflowDefinition) return;
        if (!workflowDefinition) {
            throw new Error(`Workflow with ID ${workflowDefinitionId} not found`);
        }
        siteUtility.setDocumentTitle(workflowDefinition.label);
    }, [workflowDefinitionId, workflowDefinition, isLoadingWorkflowDefinition, siteUtility]);

    const handleRemove = React.useCallback(() => {
        // navigate to site root
        siteUtility.forceNavigateTo('/');
    }, [siteUtility]);

    // const handleDuplicate = (workflowDefinition: WorkflowDefinition) => {
    //     siteUtility.forceNavigateTo(`/workflow/${workflowDefinition.id}`);
    // };

    if (isLoadingWorkflowDefinition || isLoadingWorkflowRuns || !workflowDefinition || !workflowRuns) {
        return (
            <AppView title="Workflow Runner">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView title={<Title3 className={classes.title}>{workflowDefinition.label}</Title3>}>
            <div className={classes.root}>
                <div className={classes.content}>
                    <WorkflowEdit label="Edit Workflow Definition" workflowDefinition={workflowDefinition} />
                    <WorkflowRuns workflowDefinitionId={workflowDefinitionId} workflowRuns={workflowRuns} />
                </div>
                <Toolbar className={classes.toolbar}>
                    <WorkflowRemove asToolbarButton workflowDefinition={workflowDefinition} onRemove={handleRemove} />
                    {/* // TODO: implement WorkflowExport that includes both the workflow definition and the runs */}
                    {/* <WorkflowExport asToolbarButton workflowDefinition={workflowDefinition} /> */}
                    {/* // TODO: implement WorkflowDuplicate */}
                    {/* <WorkflowDuplicate asToolbarButton workflowDefinition={workflowDefinition} onDuplicate={handleDuplicate} />  */}
                </Toolbar>
            </div>
        </AppView>
    );
};
