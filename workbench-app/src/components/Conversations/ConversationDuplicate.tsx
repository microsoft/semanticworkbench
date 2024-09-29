// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';

interface ConversationDuplicateProps {
    conversation: Conversation;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (conversationId: string) => void;
    onDuplicateError?: (error: Error) => void;
}

export const ConversationDuplicate: React.FC<ConversationDuplicateProps> = (props) => {
    const { conversation, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const workbenchService = useWorkbenchService();

    const duplicateConversation = async () => {
        try {
            const duplicate = await workbenchService.duplicateConversationsAsync([conversation.id]);
            onDuplicate?.(duplicate[0]);
        } catch (error) {
            onDuplicateError?.(error as Error);
        }
    };

    return (
        <CommandButton
            description="Duplicate conversation"
            icon={<SaveCopy24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Duplicate"
            dialogContent={{
                title: 'Duplicate conversation',
                content: <p>Are you sure you want to duplicate this conversation?</p>,
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="duplicate">
                        <Button appearance="primary" onClick={duplicateConversation}>
                            Duplicate
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
