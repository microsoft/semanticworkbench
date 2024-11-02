import { DialogTrigger } from '@fluentui/react-components';
import { ChatAddRegular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../../App/CommandButton';
import { NewConversation } from './NewConversation';

export const NewConversationButton: React.FC = () => {
    return (
        <CommandButton
            description="New Conversation with Assistant"
            icon={<ChatAddRegular />}
            iconOnly
            dialogContent={{
                title: 'New Conversation with Assistant',
                content: (
                    <NewConversation
                        dismissButton={
                            <DialogTrigger key="cancel" disableButtonEnhancement>
                                <CommandButton appearance="secondary" label="Cancel" />
                            </DialogTrigger>
                        }
                    />
                ),
                hideDismissButton: true,
            }}
        />
    );
};
