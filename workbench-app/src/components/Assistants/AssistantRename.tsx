// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useGetConversationParticipantsQuery, useUpdateAssistantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantRenameProps {
    assistant: Assistant;
    conversationId?: string;
    iconOnly?: boolean;
    simulateMenuItem?: boolean;
    onRename?: (value: string) => Promise<void>;
}

export const AssistantRename: React.FC<AssistantRenameProps> = (props) => {
    const { assistant, conversationId, iconOnly, simulateMenuItem, onRename } = props;
    const [name, setName] = React.useState(assistant.name);
    const [submitted, setSubmitted] = React.useState(false);
    const [open, setOpen] = React.useState(false);
    const [updateAssistant] = useUpdateAssistantMutation();
    const { refetch: refetchParticipants } = useGetConversationParticipantsQuery(conversationId ?? '', {
        skip: !conversationId,
    });

    const handleRename = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);
        await updateAssistant({ ...assistant, name });

        // Refetch participants to update the assistant name in the list
        if (conversationId) {
            await refetchParticipants();
        }

        await onRename?.(name);
        setOpen(false);
        setSubmitted(false);
    }, [assistant, conversationId, name, onRename, refetchParticipants, submitted, updateAssistant]);

    return (
        <CommandButton
            open={open}
            onClick={() => setOpen(true)}
            icon={<EditRegular />}
            label="Rename"
            iconOnly={iconOnly}
            simulateMenuItem={simulateMenuItem}
            description="Rename assistant"
            dialogContent={{
                title: 'Rename Assistant',
                content: (
                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            handleRename();
                        }}
                    >
                        <Field label="Name">
                            <Input disabled={submitted} value={name} onChange={(_event, data) => setName(data.value)} />
                        </Field>
                        <button disabled={!name || submitted} type="submit" hidden />
                    </form>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="rename" disableButtonEnhancement>
                        <Button disabled={!name || submitted} onClick={handleRename} appearance="primary">
                            {submitted ? 'Renaming...' : 'Rename'}
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
