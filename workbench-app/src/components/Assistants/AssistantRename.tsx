// Copyright (c) Microsoft. All rights reserved.

import { DialogTrigger, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

interface AssistantRenameProps {
    value: string;
    onRename: (value: string) => Promise<void>;
}

export const AssistantRename: React.FC<AssistantRenameProps> = (props) => {
    const { value, onRename } = props;
    const [name, setName] = React.useState(value);
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);
        await onRename(name);
        setSubmitted(false);
    };

    return (
        <CommandButton
            iconOnly
            icon={<EditRegular />}
            label="Rename"
            description="Rename assistant"
            dialogContent={{
                title: 'Rename Assistant',
                content: (
                    <Field label="Name">
                        <Input disabled={submitted} value={name} onChange={(_event, data) => setName(data.value)} />
                    </Field>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="rename" disableButtonEnhancement>
                        <CommandButton
                            disabled={!name || submitted}
                            label={submitted ? 'Renaming...' : 'Rename'}
                            onClick={handleRename}
                            appearance="primary"
                        />
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
