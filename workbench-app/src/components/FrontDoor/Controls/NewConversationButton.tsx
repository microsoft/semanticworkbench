import { Button, DialogTrigger } from '@fluentui/react-components';
import { ChatAddRegular } from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useCreateConversation } from '../../../libs/useCreateConversation';
import { useNotify } from '../../../libs/useNotify';
import { DialogControl } from '../../App/DialogControl';
import { ConversationsImport } from '../../Conversations/ConversationsImport';
import { NewConversationForm } from './NewConversationForm';

export const NewConversationButton: React.FC = () => {
    const [open, setOpen] = React.useState(false);
    const { createConversation } = useCreateConversation();
    const [isValid, setIsValid] = React.useState(false);
    const [assistantId, setAssistantId] = React.useState<string>();
    const [name, setName] = React.useState<string>();
    const [assistantServiceId, setAssistantServiceId] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);
    const { navigateToConversation } = useConversationUtility();
    const { notifyError } = useNotify();

    const handleCreate = React.useCallback(async () => {
        if (submitted || !isValid || !assistantId) {
            return;
        }

        // ensure we have a valid assistant info
        let assistantInfo: { assistantId: string } | { name: string; assistantServiceId: string } | undefined;
        if (assistantId === 'new' && name && assistantServiceId) {
            assistantInfo = { name, assistantServiceId };
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

        setOpen(false);
    }, [assistantId, assistantServiceId, createConversation, isValid, name, navigateToConversation, submitted]);

    const handleImport = React.useCallback(
        (conversationIds: string[]) => {
            if (conversationIds.length > 0) {
                navigateToConversation(conversationIds[0]);
            }
            setOpen(false);
        },
        [navigateToConversation],
    );

    const handleError = React.useCallback(
        (error: Error) =>
            notifyError({
                id: 'new-conversation-error',
                title: 'Error creating conversation',
                message: error.message,
            }),
        [notifyError],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={() => setOpen(!open)}
            trigger={<Button icon={<ChatAddRegular />} />}
            title="New Conversation with Assistant"
            content={
                <NewConversationForm
                    onSubmit={handleCreate}
                    onChange={(isValid, data) => {
                        setIsValid(isValid);
                        setAssistantId(data.assistantId);
                        setAssistantServiceId(data.assistantServiceId);
                        setName(data.name);
                    }}
                    disabled={submitted}
                />
            }
            hideDismissButton
            additionalActions={[
                <ConversationsImport
                    key="import"
                    appearance="outline"
                    onImport={handleImport}
                    onError={handleError}
                    disabled={submitted}
                />,
                <DialogTrigger key="cancel" disableButtonEnhancement>
                    <Button appearance="secondary" disabled={submitted}>
                        Cancel
                    </Button>
                </DialogTrigger>,
                <Button key="create" appearance="primary" onClick={handleCreate} disabled={!isValid || submitted}>
                    {submitted ? 'Creating...' : 'Create'}
                </Button>,
            ]}
        />
    );
};
