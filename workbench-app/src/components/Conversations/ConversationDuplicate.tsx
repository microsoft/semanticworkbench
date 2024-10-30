// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useConversationDuplicateControls = (ids: string[]) => {
    const workbenchService = useWorkbenchService();

    const duplicateConversations = async (
        onDuplicate?: (conversationId: string) => void,
        onDuplicateError?: (error: Error) => void,
    ) => {
        try {
            const duplicates = await workbenchService.duplicateConversationsAsync(ids);
            duplicates.forEach((duplicate) => onDuplicate?.(duplicate));
        } catch (error) {
            onDuplicateError?.(error as Error);
        }
    };

    const duplicateConversationForm = () => <p>Are you sure you want to duplicate this conversation?</p>;

    const duplicateConversationButton = (
        onDuplicate?: (conversationId: string) => void,
        onDuplicateError?: (error: Error) => void,
    ) => (
        <DialogTrigger disableButtonEnhancement>
            <Button appearance="primary" onClick={() => duplicateConversations(onDuplicate, onDuplicateError)}>
                Duplicate
            </Button>
        </DialogTrigger>
    );

    return {
        duplicateConversationForm,
        duplicateConversationButton,
    };
};

interface ConversationDuplicateDialogProps {
    id: string;
    onDuplicate: (conversationId: string) => void;
    onCancel: () => void;
}

export const ConversationDuplicateDialog: React.FC<ConversationDuplicateDialogProps> = (props) => {
    const { id, onDuplicate, onCancel } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls([id]);

    return (
        <DialogControl
            open={true}
            onOpenChange={onCancel}
            title="Duplicate conversation"
            content={duplicateConversationForm()}
            closeLabel="Cancel"
            additionalActions={[duplicateConversationButton(onDuplicate)]}
        />
    );
};

interface ConversationDuplicateProps {
    conversation: Conversation;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (conversationId: string) => void;
    onDuplicateError?: (error: Error) => void;
}

export const ConversationDuplicate: React.FC<ConversationDuplicateProps> = (props) => {
    const { conversation, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls([
        conversation.id,
    ]);

    return (
        <CommandButton
            description="Duplicate conversation"
            icon={<SaveCopy24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Duplicate"
            dialogContent={{
                title: 'Duplicate conversation',
                content: duplicateConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [duplicateConversationButton(onDuplicate, onDuplicateError)],
            }}
        />
    );
};
