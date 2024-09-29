// Copyright (c) Microsoft. All rights reserved.

import { Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';
import { ConversationShareList } from './ConversationShareList';

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

    const readOnly = conversation.conversationPermission !== 'read_write';

    const dialogContent = readOnly
        ? undefined
        : {
              title: 'Manage Shares for Conversation',
              content: (
                  <p>
                      <ConversationShareList conversation={conversation} />
                  </p>
              ),
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
