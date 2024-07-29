// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { AppMenu } from '../components/App/AppMenu';
import { AppView } from '../components/App/AppView';
import { ExperimentalNotice } from '../components/App/ExperimentalNotice';
import { Loading } from '../components/App/Loading';
import { MyAssistants } from '../components/Assistants/MyAssistants';
import { MyConversations } from '../components/Conversations/MyConversations';
import { MyWorkflows } from '../components/Workflows/MyWorkflows';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../services/workbench';
import { useGetWorkflowDefinitionsQuery } from '../services/workbench/workflow';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXXL,
    },
});

export const Dashboard: React.FC = () => {
    const classes = useClasses();
    const { data: assistants, error: assistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: isLoadingConversations,
    } = useGetConversationsQuery();
    const {
        data: workflowDefinitions,
        error: workflowDefinitionsError,
        isLoading: isLoadingWorkflowDefinitions,
    } = useGetWorkflowDefinitionsQuery();

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Semantic Workbench');

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    if (conversationsError) {
        const errorMessage = JSON.stringify(conversationsError);
        throw new Error(`Error loading conversations: ${errorMessage}`);
    }

    if (workflowDefinitionsError) {
        const errorMessage = JSON.stringify(workflowDefinitionsError);
        throw new Error(`Error loading workflow definitions: ${errorMessage}`);
    }

    const appMenuAction = <AppMenu />;

    if (isLoadingAssistants || isLoadingConversations || isLoadingWorkflowDefinitions) {
        return (
            <AppView title="Semantic Workbench" actions={{ items: [appMenuAction], replaceExisting: true }}>
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView title="Semantic Workbench" actions={{ items: [appMenuAction], replaceExisting: true }}>
            <div className={classes.root}>
                <ExperimentalNotice />
                <MyAssistants assistants={assistants} />
                <MyConversations conversations={conversations} participantId="me" />
                {/* <MyWorkflows workflowDefinitions={workflowDefinitions} /> */}
            </div>
        </AppView>
    );
};
