// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, MessageBar, MessageBarBody, MessageBarTitle, tokens } from '@fluentui/react-components';
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AppMenu } from '../components/App/AppMenu';
import { AppView } from '../components/App/AppView';
import { ExperimentalNotice } from '../components/App/ExperimentalNotice';
import { Loading } from '../components/App/Loading';
import { MyAssistants } from '../components/Assistants/MyAssistants';
import { MyConversations } from '../components/Conversations/MyConversations';
import { MyWorkflows } from '../components/Workflows/MyWorkflows';
import { Constants } from '../Constants';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../services/workbench';
import { useGetWorkflowDefinitionsQuery } from '../services/workbench/workflow';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXXL,
    },
    messageBars: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
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
    const localUserStateId = useAppSelector((state) => state.localUser.id);
    const navigate = useNavigate();

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Dashboard');

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

    const handleConversationCreate = React.useCallback(
        (conversation: Conversation) => {
            navigate(`/conversation/${conversation.id}`);
        },
        [navigate],
    );

    const appMenuAction = <AppMenu />;

    if (isLoadingAssistants || isLoadingConversations || isLoadingWorkflowDefinitions) {
        return (
            <AppView title="Dashboard" actions={{ items: [appMenuAction], replaceExisting: true }}>
                <Loading />
            </AppView>
        );
    }

    const myConversations = conversations?.filter((conversation) => conversation.ownerId === localUserStateId) || [];
    const conversationsSharedWithMe =
        conversations?.filter((conversation) => conversation.ownerId !== localUserStateId) || [];

    return (
        <AppView title="Dashboard" actions={{ items: [appMenuAction], replaceExisting: true }}>
            <div className={classes.root}>
                <div className={classes.messageBars}>
                    <ExperimentalNotice />
                    <MessageBar intent="info" layout="multiline">
                        <MessageBarBody>
                            <MessageBarTitle>New Feature</MessageBarTitle>
                            Try out the new conversation-first UX. &nbsp;
                            <Link to={Constants.app.conversationRedirectPath}>[view]</Link>
                        </MessageBarBody>
                    </MessageBar>
                </div>
                <MyAssistants assistants={assistants} />
                <MyConversations
                    conversations={myConversations}
                    participantId="me"
                    onCreate={handleConversationCreate}
                />
                {conversationsSharedWithMe.length > 0 && (
                    <MyConversations
                        title="Conversations Shared with Me"
                        conversations={conversationsSharedWithMe}
                        participantId="me"
                        onCreate={handleConversationCreate}
                    />
                )}
                <MyWorkflows workflowDefinitions={workflowDefinitions} />
            </div>
        </AppView>
    );
};
