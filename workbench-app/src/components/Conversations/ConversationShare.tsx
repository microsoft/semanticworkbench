// Copyright (c) Microsoft. All rights reserved.

import { Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';
import { ConversationShareList } from './ConversationShareList';

const useConversationShareControls = () => {
    return {
        shareConversationForm: (conversation: Conversation) => (
            <p>
                <ConversationShareList conversation={conversation} />
            </p>
        ),
    };
};

interface ConversationShareDialogProps {
    conversation: Conversation;
    onClose: () => void;
}

export const ConversationShareDialog: React.FC<ConversationShareDialogProps> = (props) => {
    const { conversation, onClose } = props;
    const { shareConversationForm } = useConversationShareControls();

    return (
        <DialogControl
            open={true}
            onOpenChange={onClose}
            title="Share conversation"
            content={shareConversationForm(conversation)}
        />
    );
};

interface ConversationShareProps {
    conversation: Conversation;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationShare: React.FC<ConversationShareProps> = (props) => {
    const { conversation, iconOnly, asToolbarButton } = props;
    if (!conversation) {
        throw new Error('ConversationId is required');
    }

    const { shareConversationForm } = useConversationShareControls();

    const readOnly = conversation.conversationPermission !== 'read_write';

    const dialogContent = readOnly
        ? undefined
        : {
              title: 'Manage Shares for Conversation',
              content: shareConversationForm(conversation),
          };

    return (
        <CommandButton
            icon={<Share24Regular />}
            iconOnly={iconOnly}
            disabled={readOnly}
            asToolbarButton={asToolbarButton}
            label="Share"
            description="Share conversation"
            dialogContent={dialogContent}
        />
    );
};
