// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { RewindRegular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationMessage } from '../../models/ConversationMessage';
import {
    useCreateConversationMessageMutation,
    useDeleteConversationMessageMutation,
    useGetConversationMessagesQuery,
} from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

// TODO: consider removing attachments to messages that are deleted
// and send the appropriate events to the assistants

interface RewindConversationProps {
    conversationId: string;
    message: ConversationMessage;
    onRewind?: () => void;
    disabled?: boolean;
}

export const RewindConversation: React.FC<RewindConversationProps> = (props) => {
    const { conversationId, message, onRewind, disabled } = props;
    const {
        data: messages,
        error: getMessagesError,
        isLoading: isLoadingMessages,
    } = useGetConversationMessagesQuery({ conversationId });
    const [createMessage] = useCreateConversationMessageMutation();
    const [deleteMessage] = useDeleteConversationMessageMutation();

    if (getMessagesError) {
        const errorMessage = JSON.stringify(getMessagesError);
        throw new Error(`Error loading messages: ${errorMessage}`);
    }

    const handleRewind = React.useCallback(async () => {
        if (!messages) {
            return;
        }

        // Find the index of the message to rewind to
        const messageIndex = messages.findIndex((possibleMessage) => possibleMessage.id === message.id);

        // If the message is not found, do nothing
        if (messageIndex === -1) {
            return;
        }

        // Delete all messages from the message to the end of the conversation
        for (let i = messageIndex; i < messages.length; i++) {
            await deleteMessage({ conversationId, messageId: messages[i].id });
        }

        // Call the onRewind callback
        onRewind?.();
    }, [conversationId, deleteMessage, messages, message, onRewind]);

    const handleRewindWithRedo = React.useCallback(async () => {
        await handleRewind();

        // Create a new message with the same content as the message to redo
        await createMessage({
            conversationId,
            ...message,
        });

        // Call the onRewind callback
        onRewind?.();
    }, [conversationId, createMessage, handleRewind, message, onRewind]);

    return (
        <CommandButton
            disabled={disabled || isLoadingMessages}
            description="Rewind conversation to before this message, with optional redo."
            icon={<RewindRegular />}
            iconOnly={true}
            dialogContent={{
                trigger: <Button appearance="subtle" icon={<RewindRegular />} size="small" />,
                title: 'Rewind Conversation',
                content: (
                    <>
                        <p>
                            Are you sure you want to rewind the conversation to before this message? This action cannot
                            be undone.
                        </p>
                        <p>
                            Optionally, you can choose to rewind the conversation and then redo the chosen message. This
                            will rewind the conversation to before the chosen message and then re-add the message back
                            to the conversation, effectively replaying the message.
                        </p>
                        <p>
                            <em>NOTE: This is an experimental feature.</em>
                        </p>
                        <p>
                            <em>
                                This will remove the messages from the conversation history in the Semantic Workbench,
                                but it is up to the individual assistant implementations to handle message deletion and
                                making decisions on what to do with other systems that may have received the message
                                (such as synthetic memories that may have been created or summaries, etc.)
                            </em>
                        </p>
                        <p>
                            <em>
                                Files or other data associated with the messages will not be removed from the system.
                            </em>
                        </p>
                    </>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="rewind" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleRewind}>
                            Rewind
                        </Button>
                    </DialogTrigger>,
                    <DialogTrigger key="rewindWithRedo" disableButtonEnhancement>
                        <Button onClick={handleRewindWithRedo}>Rewind with Redo</Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
