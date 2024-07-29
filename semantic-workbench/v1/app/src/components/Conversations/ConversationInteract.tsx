// Copyright (c) Microsoft. All rights reserved.

import { Chat24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Link } from 'react-router-dom';
import { Conversation } from '../../models/Conversation';
import { CommandButton } from '../App/CommandButton';

interface ConversationInteractProps {
    conversation: Conversation;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationInteract: React.FC<ConversationInteractProps> = (props) => {
    const { conversation, iconOnly, asToolbarButton } = props;

    return (
        <Link to={`/conversation/${conversation.id}`}>
            <CommandButton
                description="Enter conversation"
                icon={<Chat24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Conversation"
            />
        </Link>
    );
};
