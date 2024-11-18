// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, DialogTrigger } from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useNotify } from '../../libs/useNotify';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useConversationDuplicateControls = (id: string) => {
    const workbenchService = useWorkbenchService();
    const [submitted, setSubmitted] = React.useState(false);

    const duplicateConversation = React.useCallback(
        async (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    const duplicates = await workbenchService.duplicateConversationsAsync([id]);
                    await onDuplicate?.(duplicates[0]);
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [id, workbenchService],
    );

    const duplicateConversationForm = React.useCallback(
        () => <p>Are you sure you want to duplicate this conversation?</p>,
        [],
    );

    const duplicateConversationButton = React.useCallback(
        (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="duplicate"
                appearance="primary"
                onClick={() => duplicateConversation(onDuplicate, onError)}
                disabled={submitted}
            >
                {submitted ? 'Duplicating...' : 'Duplicate'}
            </Button>
        ),
        [duplicateConversation, submitted],
    );

    return {
        duplicateConversationForm,
        duplicateConversationButton,
    };
};

interface ConversationDuplicateDialogProps {
    conversationId: string;
    onDuplicate: (conversationId: string) => Promise<void>;
    open?: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const ConversationDuplicateDialog: React.FC<ConversationDuplicateDialogProps> = (props) => {
    const { conversationId, onDuplicate, open, onOpenChange } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls(conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'error',
                title: 'Duplicate conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Duplicate conversation"
            content={duplicateConversationForm()}
            closeLabel="Cancel"
            additionalActions={[duplicateConversationButton(onDuplicate, handleError)]}
        />
    );
};

interface ConversationDuplicateProps {
    conversationId: string;
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (conversationId: string) => Promise<void>;
    onDuplicateError?: (error: Error) => void;
}

export const ConversationDuplicate: React.FC<ConversationDuplicateProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const { duplicateConversationForm, duplicateConversationButton } = useConversationDuplicateControls(conversationId);

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
                additionalActions: [
                    <DialogTrigger key="duplicate" disableButtonEnhancement>
                        {duplicateConversationButton(onDuplicate, onDuplicateError)}
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
