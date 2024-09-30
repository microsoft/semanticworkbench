// Copyright (c) Microsoft. All rights reserved.

import { Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

interface ConversationRenameProps {
    disabled?: boolean;
    id: string;
    value: string;
    onRename: (id: string, value: string) => Promise<void>;
}

export const ConversationRename: React.FC<ConversationRenameProps> = (props) => {
    const { id, value, onRename, disabled } = props;
    const [name, setName] = React.useState(value);
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);
        await onRename(id, name);
        setSubmitted(false);
    };

    return (
        <CommandButton
            iconOnly
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename conversation"
            dialogContent={{
                title: 'Rename conversation',
                content: (
                    <Field label="Name">
                        <Input disabled={submitted} value={name} onChange={(_event, data) => setName(data.value)} />
                    </Field>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <CommandButton
                        key="rename"
                        disabled={!name || submitted}
                        label={submitted ? 'Renaming...' : 'Rename'}
                        onClick={handleRename}
                        appearance="primary"
                    />,
                ],
            }}
        />
    );
};
