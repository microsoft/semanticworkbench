// Copyright (c) Microsoft. All rights reserved.
import { makeStyles } from '@fluentui/react-components';
import { LinkRegular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationShare } from '../../models/ConversationShare';
import { CommandButton } from '../App/CommandButton';
import { ConversationShareCreate } from './ConversationShareCreate';
import { ConversationShareView } from './ConversationShareView';

const useClasses = makeStyles({
    root: {
        display: 'inline-block',
    },
});

interface MessageLinkProps {
    conversation: Conversation;
    messageId: string;
}

export const MessageLink: React.FC<MessageLinkProps> = ({ conversation, messageId }) => {
    const classes = useClasses();
    const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
    const [createdShare, setCreatedShare] = React.useState<ConversationShare | undefined>(undefined);

    if (!conversation || !messageId) {
        throw new Error('Invalid conversation or message ID');
    }

    return (
        <>
            <div className={classes.root}>
                <CommandButton
                    icon={<LinkRegular />}
                    appearance="subtle"
                    title="Share message link"
                    size="small"
                    onClick={() => setCreateDialogOpen(true)}
                />
            </div>
            {createDialogOpen && (
                <ConversationShareCreate
                    conversation={conversation}
                    linkToMessageId={messageId}
                    onCreated={(share) => setCreatedShare(share)}
                    onClosed={() => setCreateDialogOpen(false)}
                />
            )}
            {createdShare && (
                <ConversationShareView conversationShare={createdShare} onClosed={() => setCreatedShare(undefined)} />
            )}
        </>
    );
};
