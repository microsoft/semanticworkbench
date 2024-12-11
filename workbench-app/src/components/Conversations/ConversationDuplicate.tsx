// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    Radio,
    RadioGroup,
} from '@fluentui/react-components';
import { SaveCopy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useNotify } from '../../libs/useNotify';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Utility } from '../../libs/Utility';
import { useDuplicateConversationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const enum AssistantParticipantOption {
    SameAssistants = 'Include the same assistants in the new conversation.',
    CloneAssistants = 'Create copies of the assistants in the new conversation.',
}

const useConversationDuplicateControls = (id: string) => {
    const workbenchService = useWorkbenchService();
    const [assistantParticipantOption, setAssistantParticipantOption] = React.useState<AssistantParticipantOption>(
        AssistantParticipantOption.SameAssistants,
    );
    const [duplicateConversation] = useDuplicateConversationMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [title, setTitle] = React.useState('');

    const handleDuplicateConversation = React.useCallback(
        async (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    switch (assistantParticipantOption) {
                        case AssistantParticipantOption.SameAssistants:
                            const results = await duplicateConversation({ id, title }).unwrap();
                            if (results.conversationIds.length === 0) {
                                throw new Error('No conversation ID returned');
                            }
                            await onDuplicate?.(results.conversationIds[0]);
                            break;
                        case AssistantParticipantOption.CloneAssistants:
                            const duplicateIds = await workbenchService.exportThenImportConversationAsync([id]);
                            await onDuplicate?.(duplicateIds[0]);
                            break;
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [assistantParticipantOption, duplicateConversation, id, title, workbenchService],
    );

    const duplicateConversationForm = React.useCallback(
        () => (
            <>
                <Field label="Title" required={true}>
                    <Input
                        value={title}
                        onChange={(_, data) => setTitle(data.value)}
                        required={true}
                        placeholder="Enter a title for the duplicated conversation"
                    />
                </Field>
                <Field label="Assistant Duplication Options" required={true}>
                    <RadioGroup
                        defaultValue={assistantParticipantOption}
                        onChange={(_, data) => setAssistantParticipantOption(data.value as AssistantParticipantOption)}
                        required={true}
                    >
                        <Radio
                            value={AssistantParticipantOption.SameAssistants}
                            label={AssistantParticipantOption.SameAssistants}
                        />
                        <Radio
                            value={AssistantParticipantOption.CloneAssistants}
                            label={AssistantParticipantOption.CloneAssistants}
                        />
                    </RadioGroup>
                </Field>
            </>
        ),
        [assistantParticipantOption, title],
    );

    const duplicateConversationButton = React.useCallback(
        (onDuplicate?: (conversationId: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="duplicate"
                appearance="primary"
                onClick={() => handleDuplicateConversation(onDuplicate, onError)}
                disabled={submitted}
            >
                {submitted ? 'Duplicating...' : 'Duplicate'}
            </Button>
        ),
        [handleDuplicateConversation, submitted],
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
