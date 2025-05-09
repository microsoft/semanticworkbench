// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Subtitle2, Title3, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useCreateConversation } from '../../libs/useCreateConversation';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetAssistantServiceInfosQuery } from '../../services/workbench';
import { ExperimentalNotice } from '../App/ExperimentalNotice';
import { Loading } from '../App/Loading';
import { ConversationsImport } from '../Conversations/ConversationsImport';
import { Chat } from './Chat/Chat';
import { AssistantCard } from './Controls/AssistantCard';
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
        maxWidth: '900px',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
        height: '100%',
    },
    assistantHeader: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        alignItems: 'center',
        width: '100%',
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
    cards: {
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'center',
        gap: tokens.spacingVerticalL,
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    card: {
        padding: 0,
        width: '420px',
    },
    cardHeader: {
        padding: tokens.spacingHorizontalM,
        borderRadius: tokens.borderRadiusMedium,
        borderBottomRightRadius: 0,
        borderBottomLeftRadius: 0,
    },
    cardHeaderBody: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxSizing: 'border-box',
        width: '100%',
    },
    cardPreview: {
        padding: tokens.spacingHorizontalM,
        paddingBottom: tokens.spacingVerticalL,
        margin: '0 !important',
        width: '100%',
        boxSizing: 'border-box',
        wordWrap: 'break-word',
        overflowWrap: 'break-word',
        '& ul': {
            boxSizing: 'border-box',
        },
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
    const { isFetching: createConversationIsFetching } = useCreateConversation();
    const { data: assistantServices } = useGetAssistantServiceInfosQuery({ userIds: ['me'] });

    const classes = useClasses();

    React.useEffect(() => {
        if (!activeConversationId && document.title !== Constants.app.name) {
            siteUtility.setDocumentTitle();
        }
    }, [activeConversationId, siteUtility]);

    const createConversationWithAssistant = React.useCallback(
        async (
            assistantInfo:
                | { assistantId: string }
                | { name: string; assistantServiceId: string; templateId: string; image?: string },
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

    const uniqueAssistantTemplates = React.useMemo(
        () =>
            assistantServices
                ?.flatMap((assistantService) => {
                    return assistantService.templates.map((template) => ({
                        assistantServiceId: assistantService.assistantServiceId,
                        templateId: template.id,
                        name: template.name,
                    }));
                })
                .toSorted((a, b) => a.name.localeCompare(b.name)) ?? [],
        [assistantServices],
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
                        <div className={classes.assistantHeader}>
                            <Title3>Choose an assistant</Title3>
                        </div>
                        <div className={classes.cards}>
                            {uniqueAssistantTemplates?.map((ids) => (
                                <AssistantCard
                                    key={ids.assistantServiceId + '/' + ids.templateId}
                                    assistantServiceId={ids.assistantServiceId}
                                    templateId={ids.templateId}
                                />
                            ))}
                        </div>
                        <div className={classes.form}>
                            <Subtitle2>Or pick from your list of assistants:</Subtitle2>
                            <NewConversationForm
                                assistantFieldLabel=""
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
