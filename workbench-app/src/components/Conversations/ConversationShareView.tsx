// Copyright (c) Microsoft. All rights reserved.

import {
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    Field,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { ConversationShare } from '../../models/ConversationShare';
import { CopyButton } from '../App/CopyButton';
import { DialogControl } from '../App/DialogControl';

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
        <DialogControl
            defaultOpen={true}
            onOpenChange={handleOpenChange}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            title="Share link details"
            content={
                <>
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
                </>
            }
        />
    );
};
