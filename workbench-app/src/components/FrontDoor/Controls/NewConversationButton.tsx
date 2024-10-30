import { DialogTrigger } from '@fluentui/react-components';
import { ChatAddRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../../App/CommandButton';
import { useCreateConversationControls } from './useCreateConversationControls';

export const NewConversationButton: React.FC = () => {
    const { createConversationForm, createConversationSubmitButton } = useCreateConversationControls();

    return (
        <CommandButton
            description="New Conversation with Assistant"
            icon={<ChatAddRegular />}
            iconOnly
            dialogContent={{
                title: 'New Conversation',
                content: createConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="create" disableButtonEnhancement>
                        {createConversationSubmitButton()}
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
