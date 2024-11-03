import { Button, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
import { ConversationsImport } from '../../Conversations/ConversationsImport';
import { NewConversationForm } from './NewConversationForm';

const useClasses = makeStyles({
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    serviceOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'end',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

interface NewConversationProps {
    onCreate?: (conversationId: string) => void;
    onImport?: (conversationIds: string[]) => void;
    dismissButton?: React.ReactNode;
}

export const NewConversation: React.FC<NewConversationProps> = (props) => {
    const { onCreate, onImport, dismissButton } = props;
    const classes = useClasses();
    const { createConversation } = useCreateConversation();

    const [isValid, setIsValid] = React.useState(false);
    const [title, setTitle] = React.useState<string>();
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();

    const resetState = React.useCallback(() => {
        setTitle(undefined);
        setAssistantId(undefined);
        setName(undefined);
        setAssistantServiceId(undefined);
    }, []);

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !title || !assistantId || !(assistantId === 'new' && name && assistantServiceId)) {
            return;
        }

        setSubmitted(true);

        const assistantInfo: { assistantId: string } | { name: string; assistantServiceId: string } =
            assistantId === 'new' ? { name, assistantServiceId } : { assistantId };

        try {
            const { conversation } = await createConversation(title, assistantInfo);
            navigateToConversation(conversation.id);
        } finally {
            // In case of error, allow user to retry
            setSubmitted(false);
        }

        // Callback
        onCreate?.(assistantId);

        // Reset form
        resetState();
    }, [
        assistantId,
        assistantServiceId,
        createConversation,
        isValid,
        name,
        navigateToConversation,
        onCreate,
        resetState,
        submitted,
        title,
    ]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
            onImport?.(conversationIds);

            // Reset form
            resetState();
        },
        [navigateToConversation, onImport, resetState],
    );

    return (
        <div className={classes.content}>
            <NewConversationForm
                onSubmit={handleCreate}
                onChange={(isValid, data) => {
                    setIsValid(isValid);
                    setTitle(data.title);
                    setAssistantId(data.assistantId);
                    setAssistantServiceId(data.assistantServiceId);
                    setName(data.name);
                }}
                disabled={submitted}
            />
            <div className={classes.actions}>
                <ConversationsImport appearance="outline" onImport={handleImport} disabled={submitted} />
                {dismissButton}
                <Button appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                    New Conversation
                </Button>
            </div>
        </div>
    );
};
