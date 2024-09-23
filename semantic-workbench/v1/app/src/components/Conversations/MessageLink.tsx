// Copyright (c) Microsoft. All rights reserved.
import { makeStyles } from '@fluentui/react-components';
import { LinkRegular } from '@fluentui/react-icons';
import React from 'react';
import { useCreateShareMutation } from '../../services/workbench/share';
import { CopyButton } from '../App/CopyButton';

const useClasses = makeStyles({
    root: {
        display: 'inline-block',
    },
});

interface MessageLinkProps {
    readOnly: boolean;
    conversationId: string;
    messageId: string;
}

export const MessageLink: React.FC<MessageLinkProps> = ({ conversationId, messageId, readOnly }) => {
    const classes = useClasses();
    const [createShare] = useCreateShareMutation();

    if (!conversationId || !messageId) {
        throw new Error('Invalid conversation or message ID');
    }

    const getLink = React.useCallback(async () => {
        if (readOnly) {
            return `${window.location.origin}/conversation/${conversationId}#${messageId}`;
        }

        const share = await createShare({
            conversationId,
            label: 'Message link',
            conversationPermission: 'read_write',
            metadata: {
                openMessageAction: messageId,
                showDuplicateAction: false,
                showJoinAction: false,
            },
        }).unwrap();
        return `${window.location.origin}/conversation-share/${encodeURIComponent(share.id)}/redeem`;
    }, [createShare, conversationId, messageId, readOnly]);

    return (
        <div className={classes.root}>
            <CopyButton
                icon={<LinkRegular />}
                appearance="subtle"
                data={getLink}
                tooltip="Copy message link"
                size="small"
            />
        </div>
    );
};
