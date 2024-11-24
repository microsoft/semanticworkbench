// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { ExperimentalNotice } from '../components/App/ExperimentalNotice';
import { Loading } from '../components/App/Loading';
import { MyAssistants } from '../components/Assistants/MyAssistants';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    messageBars: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    body: {
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

    const handleConversationCreate = React.useCallback(
        (conversation: Conversation) => {
            navigate(`/conversation/${conversation.id}`);
        },
        [navigate],
    );

    if (isLoadingAssistants || isLoadingConversations) {
        return (
            <AppView title="Dashboard">
                <Loading />
            </AppView>
        );
    }

    const myConversations = conversations?.filter((conversation) => conversation.ownerId === localUserStateId) || [];
    const conversationsSharedWithMe =
        conversations?.filter((conversation) => conversation.ownerId !== localUserStateId) || [];

    return (
        <AppView title="Dashboard">
            <div className={classes.root}>
                <div className={classes.messageBars}>
                    <ExperimentalNotice />
                </div>
                <div className={classes.body}>
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
                </div>
            </div>
        </AppView>
    );
};
