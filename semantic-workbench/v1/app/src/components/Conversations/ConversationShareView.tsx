// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Field,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { ConversationShare } from '../../models/ConversationShare';
import { CopyButton } from '../App/CopyButton';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    shareLink: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        ...shorthands.padding(tokens.spacingVerticalXXS, 0, tokens.spacingVerticalXXS),
    },
});

interface ConversationShareViewProps {
    conversationShare: ConversationShare;
    showDetails?: boolean;
    onClosed?: () => void;
}

export const ConversationShareView: React.FC<ConversationShareViewProps> = (props) => {
    const { conversationShare, onClosed, showDetails } = props;
    const conversationUtility = useConversationUtility();
    const classes = useClasses();

    const { shareType, linkToMessageId } = conversationUtility.getShareType(conversationShare);
    const link = conversationUtility.getShareLink(conversationShare);

    const handleOpenChange = React.useCallback(
        (_: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                onClosed?.();
            }
        },
        [onClosed],
    );

    const linkToConversation = (conversationId: string) => `${window.location.origin}/conversation/${conversationId}`;

    return (
        <Dialog defaultOpen={true} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Share link details</DialogTitle>
                    <DialogContent className={classes.dialogContent}>
                        <Field label="Share label">
                            <strong>{conversationShare.label}</strong>
                        </Field>
                        <Field label="Share link">
                            <div className={classes.shareLink}>
                                <a href={link}>{link}</a>
                                <CopyButton appearance="primary" data={link} tooltip="Copy share link" />
                            </div>
                        </Field>
                        {showDetails && (
                            <>
                                <Field label="Conversation">
                                    <a href={linkToConversation(conversationShare.conversationId)}>
                                        {conversationShare.conversationTitle}
                                    </a>
                                </Field>
                                {linkToMessageId && <Field label="Links to message">{linkToMessageId}</Field>}
                                <Field label="Permission">{shareType.toString()}</Field>
                                <Field label="Created">
                                    {new Date(Date.parse(conversationShare.createdDateTime + 'Z')).toLocaleString()}
                                </Field>
                            </>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <DialogTrigger>
                            <Button>Close</Button>
                        </DialogTrigger>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
