// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, shorthands, Title3, tokens } from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../../Constants';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useCreateConversation } from '../../libs/useCreateConversation';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { useAppSelector } from '../../redux/app/hooks';
import { ExperimentalNotice } from '../App/ExperimentalNotice';
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
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        width: '100%',
        maxWidth: '550px',
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
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

    if (activeConversationId) {
        return <Chat conversationId={activeConversationId} headerBefore={headerBefore} headerAfter={headerAfter} />;
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
                            <ConversationsImport appearance="outline" onImport={handleImport} disabled={submitted} />
                            <Button appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                                Create
                            </Button>
                        </div>
                    </div>
                </div>
            </>
        </div>
    );
};
