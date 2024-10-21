// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppMenu } from '../components/App/AppMenu';
import { ExperimentalNotice } from '../components/App/ExperimentalNotice';
import { Loading } from '../components/App/Loading';
import { MyAssistants } from '../components/Assistants/MyAssistants';
import { MyConversations } from '../components/Conversations/MyConversations';
import { useLocalUserAccount } from '../libs/useLocalUserAccount';
import { useSiteUtility } from '../libs/useSiteUtility';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import { setActiveConversationId } from '../redux/features/app/appSlice';
import { useGetAssistantsQuery, useGetConversationsQuery } from '../services/workbench';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        height: '100vh',
        gridTemplateAreas: `
            "leftRail main rightRail"
        `,
    },
    flyoutButton: {
        position: 'absolute',
        top: tokens.spacingVerticalXS,
        right: tokens.spacingHorizontalXS,
        zIndex: tokens.zIndexFloating,
    },
    loading: {
        gridArea: 'leftRail main rightRail',
        position: 'fixed',
        top: '0',
        left: '0',
        bottom: '0',
        right: '0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    leftRail: {
        gridArea: 'leftRail',
        borderRight: `1px solid ${tokens.colorNeutralBackground2}`,
        transition: 'width 0.2s',
        overflow: 'auto',
        minWidth: '200px',
        maxWidth: '300px',
        flexShrink: 0,
    },
    main: {
        gridArea: 'main',
        overflow: 'auto',
        padding: tokens.spacingHorizontalM,
    },
    rightRail: {
        gridArea: 'rightRail',
        borderLeft: `1px solid ${tokens.colorNeutralBackground2}`,
        transition: 'width 0.2s',
        overflow: 'auto',
        minWidth: '200px',
        maxWidth: '300px',
        flexShrink: 0,
    },
    collapse: {
        width: '60px', // narrow view
    },
});

export const FrontDoor: React.FC = () => {
    const { conversationId } = useParams();
    const classes = useClasses();
    const { activeConversationId, completedFirstRun } = useAppSelector((state) => state.app);
    const navigate = useNavigate();

    const [leftRailCollapsed, setLeftRailCollapsed] = React.useState(false);
    const [rightRailCollapsed, setRightRailCollapsed] = React.useState(false);

    const { data: assistants, error: assistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: isLoadingConversations,
    } = useGetConversationsQuery();
    const { getUserId } = useLocalUserAccount();

    React.useEffect(() => {
        if (!completedFirstRun?.app && window.location.pathname !== '/terms') {
            navigate('/terms');
        }
    }, [completedFirstRun, navigate]);

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Dashboard');

    if (conversationId) {
        if (activeConversationId !== conversationId) {
            setActiveConversationId(conversationId);
        }
    }

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

    const appMenuAction = <AppMenu />;

    if (isLoadingAssistants || isLoadingConversations) {
        return (
            <div id="app" className={classes.root}>
                <div className={classes.loading}>
                    <Loading />
                </div>
            </div>
        );
    }

    const userId = getUserId();
    const myConversations = conversations?.filter((conversation) => conversation.ownerId === userId) || [];
    const conversationsSharedWithMe = conversations?.filter((conversation) => conversation.ownerId !== userId) || [];

    return (
        <div id="app" className={classes.root}>
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button className={classes.flyoutButton} appearance="primary">
                        Menu
                    </Button>
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem>Profile</MenuItem>
                        <MenuItem>Settings</MenuItem>
                        <MenuItem>Privacy & Cookies</MenuItem>
                        <MenuItem>Sign Out</MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
            <div
                className={`${classes.leftRail} ${leftRailCollapsed ? classes.collapse : ''}`}
                onMouseEnter={() => setLeftRailCollapsed(false)}
                onMouseLeave={() => setLeftRailCollapsed(true)}
            >
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
                <button onClick={() => setLeftRailCollapsed(!leftRailCollapsed)}>Toggle Left Rail</button>
            </div>
            <div className={classes.main}>
                <ExperimentalNotice />
                <h1>Main Content Area</h1>
            </div>
            <div
                className={`${classes.rightRail} ${rightRailCollapsed ? classes.collapse : ''}`}
                onMouseEnter={() => setRightRailCollapsed(false)}
                onMouseLeave={() => setRightRailCollapsed(true)}
            >
                <button onClick={() => setRightRailCollapsed(!rightRailCollapsed)}>Toggle Right Rail</button>
            </div>
        </div>
    );
};
