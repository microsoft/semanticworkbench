// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { Delete16Regular, Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { ConversationMessage } from '../../models/ConversationMessage';
import { useDeleteConversationMessageMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface MessageDeleteProps {
    conversationId: string;
    message: ConversationMessage;
    onDelete?: (message: ConversationMessage) => void;
    disabled?: boolean;
}

export const MessageDelete: React.FC<MessageDeleteProps> = (props) => {
    const { conversationId, message, onDelete, disabled } = props;
    const [deleteMessage] = useDeleteConversationMessageMutation();

    const handleDelete = React.useCallback(async () => {
        await deleteMessage({ conversationId, messageId: message.id });

        onDelete?.(message);
    }, [conversationId, deleteMessage, message, onDelete]);

    return (
        <CommandButton
            description="Delete message"
            icon={<Delete24Regular />}
            iconOnly={true}
            disabled={disabled}
            dialogContent={{
                trigger: <Button appearance="subtle" icon={<Delete16Regular />} size="small" />,
                title: 'Delete Message',
                content: (
                    <>
                        <p>Are you sure you want to delete this message? This action cannot be undone.</p>
                        <p>
                            <em>
                                NOTE: This is an experimental feature. This will remove the message from the
                                conversation history in the Semantic Workbench, but it is up to the individual assistant
                                implementations to handle message deletion and making decisions on what to do with other
                                systems that may have received the message (such as synthetic memories that may have
                                been created or summaries, etc.)
                            </em>
                        </p>
                    </>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <Button appearance="primary" onClick={handleDelete}>
                            Delete
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
