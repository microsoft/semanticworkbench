// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    makeStyles,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    shorthands,
    SplitButton,
    Subtitle2,
    Title3,
    tokens,
} from '@fluentui/react-components';
import { ChatAdd24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Constants } from '../../Constants';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useCreateConversation } from '../../libs/useCreateConversation';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { Assistant } from '../../models/Assistant';
import { useAppSelector } from '../../redux/app/hooks';
import { ExperimentalNotice } from '../App/ExperimentalNotice';
import { Loading } from '../App/Loading';
import { ConversationsImport } from '../Conversations/ConversationsImport';
import { Chat } from './Chat/Chat';
import { NewConversationForm } from './Controls/NewConversationForm';

const useClasses = makeStyles({
    root: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    header: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    body: {
        flex: '1 1 auto',
        display: 'flex',
        justifyContent: 'center',
        height: '90vh',
        marginBottom: tokens.spacingVerticalL,
        overflowY: 'auto',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        maxWidth: '550px',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        height: '100%',
    },
    assistantHeader: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
        marginTop: tokens.spacingVerticalL,
    },
    form: {
        marginTop: tokens.spacingVerticalL,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

interface MainContentProps {
    headerBefore?: React.ReactNode;
    headerAfter?: React.ReactNode;
}

export const MainContent: React.FC<MainContentProps> = (props) => {
    const { headerBefore, headerAfter } = props;
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const { createConversation } = useCreateConversation();
    const [isValid, setIsValid] = React.useState(false);
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [templateId, setTemplateId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();
    const siteUtility = useSiteUtility();
    const { isFetching: createConversationIsFetching, assistants } = useCreateConversation();

    const classes = useClasses();

    React.useEffect(() => {
        if (!activeConversationId && document.title !== Constants.app.name) {
            siteUtility.setDocumentTitle();
        }
    }, [activeConversationId, siteUtility]);

    const createConversationWithAssistant = React.useCallback(
        async (
            assistantInfo: { assistantId: string } | { name: string; assistantServiceId: string; templateId: string },
        ) => {
            setSubmitted(true);
            try {
                const { conversation } = await createConversation(assistantInfo);
                navigateToConversation(conversation.id);
            } finally {
                setSubmitted(false);
            }
        },
        [createConversation, navigateToConversation],
    );

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !assistantId) {
            return;
        }

        // ensure we have a valid assistant info
        let assistantInfo:
            | { assistantId: string }
            | { name: string; assistantServiceId: string; templateId: string }
            | undefined;
        if (assistantId === 'new' && name && assistantServiceId && templateId) {
            assistantInfo = { name, assistantServiceId, templateId };
        } else {
            assistantInfo = { assistantId };
        }

        if (!assistantInfo) {
            return;
        }

        await createConversationWithAssistant(assistantInfo);
    }, [assistantId, assistantServiceId, createConversationWithAssistant, isValid, name, submitted, templateId]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
        },
        [navigateToConversation],
    );

    const handleQuickCreate = React.useCallback(
        (assistant: Assistant) => {
            return async () => {
                await createConversationWithAssistant({
                    assistantId: assistant.id,
                });
            };
        },
        [createConversationWithAssistant],
    );

    const quickAssistantCreateButton = React.useCallback(
        (assistants: Assistant[] | undefined) => {
            if (!assistants || assistants.length === 0) {
                return <></>;
            }
            if (assistants.length === 1) {
                return (
                    <Button
                        appearance="primary"
                        onClick={handleQuickCreate(assistants[0])}
                        disabled={submitted}
                        icon={<ChatAdd24Regular />}
                    >
                        New conversation
                    </Button>
                );
            }
            return (
                <Menu positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        {(triggerProps: MenuButtonProps) => (
                            <SplitButton
                                appearance="primary"
                                menuButton={triggerProps}
                                primaryActionButton={{
                                    onClick: handleQuickCreate(assistants[0]),
                                }}
                                disabled={submitted}
                                icon={<ChatAdd24Regular />}
                            >
                                New conversation
                            </SplitButton>
                        )}
                    </MenuTrigger>

                    <MenuPopover>
                        <MenuList>
                            {assistants.map((assistant) => (
                                <MenuItem
                                    key={assistant.id}
                                    onClick={handleQuickCreate(assistant)}
                                    disabled={submitted}
                                >
                                    {assistant.name}
                                </MenuItem>
                            ))}
                        </MenuList>
                    </MenuPopover>
                </Menu>
            );
        },
        [handleQuickCreate, submitted],
    );

    const getAssistants = React.useCallback(
        (serviceId: string, templateId: string) => {
            const matches = assistants?.filter(
                (assistant) => assistant.assistantServiceId === serviceId && assistant.templateId === templateId,
            );

            if (matches && matches.length > 0) {
                return matches;
            }
            return undefined;
        },
        [assistants],
    );

    if (activeConversationId) {
        return <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />;
    }

    if (createConversationIsFetching) {
        return <Loading />;
    }

    return (
        <div className={classes.root}>
            <>
                <div className={classes.header}>
                    {headerBefore}
                    <ExperimentalNotice />
                    {headerAfter}
                </div>
                <div className={classes.body}>
                    <div className={classes.content}>
                        <Title3>Create a new conversation with an assistant</Title3>
                        {getAssistants('codespace-assistant.made-exploration-team', 'workspace') && (
                            <>
                                <div className={classes.assistantHeader}>
                                    <Title3>Document Assistant</Title3>
                                    {quickAssistantCreateButton(
                                        getAssistants('codespace-assistant.made-exploration-team', 'workspace'),
                                    )}
                                </div>
                                Document Assistant is focused on reliable document creation and editing, grounded in all
                                of your context across files and the conversation.
                                <ul>
                                    <li>
                                        <b>Guidance:</b> Helps users provide the right context and get started.
                                    </li>
                                    <li>
                                        <b>Document creation and editing:</b> Creates and edits documents in a
                                        side-by-side experience all through chat, with the option of manual editing.
                                    </li>
                                    <li>
                                        <b>Rightsized autonomy:</b> Depending on your task, searches and integrates
                                        results of other actions into your documents without your intervention.
                                    </li>
                                </ul>
                            </>
                        )}
                        {getAssistants('project-assistant.made-exploration', 'context_transfer') && (
                            <>
                                <div className={classes.assistantHeader}>
                                    <Title3>Context Transfer Assistant</Title3>
                                    {quickAssistantCreateButton(
                                        getAssistants('project-assistant.made-exploration', 'context_transfer'),
                                    )}
                                </div>
                                Context Transfer Assistant bridges knowledge gaps between experts and learners through
                                dedicated roles that optimize information exchange.
                                <ul>
                                    <li>
                                        <b>Knowledge Owner Space:</b> Where experts organize and share complex
                                        information
                                    </li>
                                    <li>
                                        <b>Recipient Workspaces:</b> Where learners explore content and ask questions
                                    </li>
                                    <li>
                                        <b>Auto-Organized Knowledge:</b> Extracts and structures information from expert
                                        conversations
                                    </li>
                                    <li>
                                        <b>Question Framework:</b> System for recipients to request clarification on
                                        complex topics
                                    </li>
                                    <li>
                                        <b>Resource Sharing:</b> Documents from experts instantly appear for all
                                        recipients
                                    </li>
                                    <li>
                                        <b>Conversation Access:</b> Recipients can view expert-assistant discussions for
                                        context
                                    </li>
                                    <li>
                                        <b>Simplified Interface:</b> Tools focused on knowledge transfer rather than
                                        project tracking
                                    </li>
                                    <li>
                                        <b>Learning-Optimized Design:</b> Removes management overhead to focus on
                                        understanding
                                    </li>
                                </ul>
                            </>
                        )}
                        {getAssistants('project-assistant.made-exploration', 'default') && (
                            <>
                                <div className={classes.assistantHeader}>
                                    <Title3>Project Assistant</Title3>
                                    {quickAssistantCreateButton(
                                        getAssistants('project-assistant.made-exploration', 'default'),
                                    )}
                                </div>
                                Project Assistant connects project leaders and team members through specialized roles
                                that streamline collaboration and information sharing.
                                <ul>
                                    <li>
                                        <b>Coordinator Hub:</b> Central workspace for leaders to define goals, set
                                        direction, and resolve team blockers.
                                    </li>
                                    <li>
                                        <b>Team Workspaces:</b> Connected environments where members track progress and
                                        request clarification.
                                    </li>
                                    <li>
                                        <b>Automatic Updates:</b> Changes by coordinators instantly reach all team
                                        members.
                                    </li>
                                    <li>
                                        <b>Structured Requests:</b> Clear channel for team members to ask questions and
                                        seek guidance.
                                    </li>
                                    <li>
                                        <b>Role-Based Tools:</b> Different commands and permissions based on project
                                        responsibilities.
                                    </li>
                                    <li>
                                        <b>File Synchronization:</b> Documents shared by coordinators appear in all team
                                        workspaces.
                                    </li>
                                    <li>
                                        <b>Cross-Role Visibility:</b> See team progress (coordinator) and coordinator
                                        insights (team).
                                    </li>
                                    <li>
                                        <b>Unified Progress View:</b> Aggregates completion status from all team
                                        members.
                                    </li>
                                </ul>
                            </>
                        )}
                        {getAssistants('codespace-assistant.made-exploration-team', 'default') && (
                            <>
                                <div className={classes.assistantHeader}>
                                    <Title3>Codespace Assistant</Title3>
                                    {quickAssistantCreateButton(
                                        getAssistants('codespace-assistant.made-exploration-team', 'default'),
                                    )}
                                </div>
                                Codespace Assistant supports you with your coding and development projects.
                                <ul>
                                    <li>
                                        <b>Explore your code:</b> share files, snippets, or describe what you are
                                        working on and explore together.
                                    </li>
                                    <li>
                                        <b>Debug and refine:</b> can help troubleshoot issues and suggest improvements.
                                    </li>
                                    <li>
                                        <b>Generate solutions:</b> ask for code snippets, algorithms, or implementation
                                        ideas.
                                    </li>
                                    <li>
                                        <b>Learn and understand:</b> can explain concepts, patterns, and approaches.
                                    </li>
                                </ul>
                            </>
                        )}
                        <div className={classes.form}>
                            <Subtitle2>Or pick from your list of assistants:</Subtitle2>
                            <NewConversationForm
                                onSubmit={handleCreate}
                                onChange={(isValid, data) => {
                                    setIsValid(isValid);
                                    setAssistantId(data.assistantId);
                                    setAssistantServiceId(data.assistantServiceId);
                                    setTemplateId(data.templateId);
                                    setName(data.name);
                                }}
                                disabled={submitted}
                            />
                            <div className={classes.actions}>
                                <ConversationsImport
                                    appearance="outline"
                                    onImport={handleImport}
                                    disabled={submitted}
                                />
                                <Button appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                                    Create
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </>
        </div>
    );
};
