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
        setSubmitted(true);

        try {
            const { conversation } = await createConversation(assistantInfo);
            navigateToConversation(conversation.id);
        } finally {
            // In case of error, allow user to retry
            setSubmitted(false);
        }
    }, [
        assistantId,
        assistantServiceId,
        createConversation,
        isValid,
        name,
        navigateToConversation,
        submitted,
        templateId,
    ]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
        },
        [navigateToConversation],
    );

    const handleQuickCreate = React.useCallback(
        (assistant: Assistant | undefined) => {
            if (!assistant) {
                return () => {};
            }
            return () => {
                setIsValid(true);
                setAssistantId(assistant.id);
                handleCreate();
            };
        },
        [handleCreate],
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
                        {/* {getAssistants('project-assistant.made-exploration', 'context_transfer') && (
                            <>
                                <div className={classes.assistantHeader}>
                                    <Title3>Context Transfer Assistant</Title3>
                                    {quickAssistantCreateButton(
                                        getAssistants('project-assistant.made-exploration', 'context_transfer'),
                                    )}
                                </div>
                                Context Transfer Assistant helps you capture and share complex information, turning it
                                into interactive knowledge that others can easily explore and understand.
                                <ul>
                                    <li>
                                        <b>Thought Organization:</b> Assists in organizing your thoughts from documents,
                                        code, research papers, or brainstorming sessions.
                                    </li>
                                    <li>
                                        <b>Shared Understanding:</b> Engages with you to ensure alignment on essential
                                        information by asking pertinent questions.
                                    </li>
                                    <li>
                                        <b>Interactive Knowledge:</b> Transforms your knowledge into an interactive
                                        format to explore the rationale behind decisions and alternatives.
                                    </li>
                                    <li>
                                        <b>File Synchronization:</b> Automatically shares and updates files across
                                        participant conversations using shared links.
                                    </li>
                                    <li>
                                        <b>Shareable Experiences:</b> Enables the creation of shareable links for others
                                        to self-explore the prepared knowledge spaces.
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
                                Project Assistant is designed to help teams collaborate effectively by facilitating
                                conversations and file sharing within and across projects.
                                <ul>
                                    <li>
                                        <b>Project Coordination:</b> Acts as a personal conversation space for project
                                        coordinators.
                                    </li>
                                    <li>
                                        <b>Team Collaboration:</b> Allows easy invitation of team members to join
                                        project discussions using shareable links.
                                    </li>
                                    <li>
                                        <b>Project Brief Management:</b> Helps you create and update project briefs with
                                        goals and details.
                                    </li>
                                    <li>
                                        <b>File Synchronization:</b> Automatically shares and updates files across
                                        participant conversations using shared links, keeping everyone aligned.
                                    </li>
                                    <li>
                                        <b>Content Creation Support:</b> Capable of producing markdown, code snippets,
                                        and other types of content to support projects.
                                    </li>
                                </ul>
                            </>
                        )} */}
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
