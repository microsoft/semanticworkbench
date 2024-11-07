// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { RewindRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

// TODO: consider removing attachments to messages that are deleted
// and send the appropriate events to the assistants

interface RewindConversationProps {
    onRewind?: (redo: boolean) => void;
    disabled?: boolean;
}

export const RewindConversation: React.FC<RewindConversationProps> = (props) => {
    const { onRewind, disabled } = props;

    const handleRewind = React.useCallback(async () => onRewind?.(false), [onRewind]);
    const handleRewindWithRedo = React.useCallback(async () => onRewind?.(true), [onRewind]);

    return (
        <CommandButton
            disabled={disabled}
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
