// Copyright (c) Microsoft. All rights reserved.

import { Button, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { useUpdateConversationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

export const useConversationRenameControls = (id: string, value: string) => {
    const [updateConversation] = useUpdateConversationMutation();
    const [newTitle, setNewTitle] = React.useState(value);
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = async (onRename?: (id: string, value: string) => Promise<void>) => {
        if (submitted) {
            return;
        }
        setSubmitted(true);
        await updateConversation({ id, title: newTitle });

        if (onRename) {
            await onRename(id, newTitle);
        }

        setSubmitted(false);
    };

    const renameConversationForm = (onRename?: (id: string, value: string) => Promise<void>) => (
        <form
            onSubmit={(event) => {
                event.preventDefault();
                handleRename(onRename);
            }}
        >
            <Field label="Title">
                <Input disabled={submitted} value={newTitle} onChange={(_event, data) => setNewTitle(data.value)} />
            </Field>
        </form>
    );

    const renameConversationButton = (onRename?: (id: string, value: string) => Promise<void>) => (
        <Button disabled={!newTitle || submitted} onClick={() => handleRename(onRename)} appearance="primary">
            {submitted ? 'Renaming...' : 'Rename'}
        </Button>
    );

    return {
        renameConversationForm,
        renameConversationButton,
    };
};

interface ConversationRenameDialogProps {
    id: string;
    value: string;
    onRename: (id: string, value: string) => Promise<void>;
    onCancel: () => void;
}

export const ConversationRenameDialog: React.FC<ConversationRenameDialogProps> = (props) => {
    const { id, value, onRename, onCancel } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(id, value);

    return (
        <DialogControl
            open={true}
            onOpenChange={onCancel}
            title="Rename conversation"
            content={renameConversationForm(onRename)}
            closeLabel="Cancel"
            additionalActions={[renameConversationButton(onRename)]}
        />
    );
};

interface ConversationRenameProps {
    disabled?: boolean;
    id: string;
    value: string;
    onRename?: (id: string, value: string) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRename: React.FC<ConversationRenameProps> = (props) => {
    const { id, value, onRename, disabled, iconOnly, asToolbarButton } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(id, value);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename conversation"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: 'Rename conversation',
                content: renameConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [renameConversationButton(onRename)],
            }}
        />
    );
};
