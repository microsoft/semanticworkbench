// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
} from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { ConversationShareType, useConversationUtility } from '../libs/useConversationUtility';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useWorkbenchService } from '../libs/useWorkbenchService';
import { useRemoveConversationParticipantMutation } from '../services/workbench';
import { useGetShareQuery, useRedeemShareMutation } from '../services/workbench/share';

export const ShareRedeem: React.FC = () => {
    const { conversationShareId } = useParams();
    const navigate = useNavigate();
    const workbenchService = useWorkbenchService();
    const [redeemShare] = useRedeemShareMutation();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [messageId, setMessageId] = React.useState<string | undefined>(undefined);
    const conversationUtility = useConversationUtility();

    if (!conversationShareId) {
        throw new Error('Conversation Share ID is required');
    }

    const siteUtility = useSiteUtility();
    const {
        data: conversationShare,
        error: conversationShareError,
        isLoading: conversationIsLoading,
    } = useGetShareQuery(conversationShareId);

    const title = 'Open a shared conversation';
    siteUtility.setDocumentTitle(title);

    const handleClickJoin = React.useCallback(async () => {
        if (!conversationShare) {
            return;
        }
        setSubmitted(true);
        try {
            await redeemShare(conversationShareId);
            const hash = messageId ? `#${messageId}` : '';
            navigate(`/conversation/${conversationShare.conversationId}${hash}`, { replace: true });
        } finally {
            setSubmitted(false);
        }
    }, [conversationShare, redeemShare, conversationShareId, messageId, navigate]);

    const handleClickDuplicate = React.useCallback(async () => {
        if (!conversationShare) {
            return;
        }
        setSubmitted(true);
        try {
            // join the conversation
            const redemption = await redeemShare(conversationShare.id).unwrap();

            // duplicate it
            const duplicatedConversationIds = await workbenchService.duplicateConversationsAsync([
                redemption.conversationId,
            ]);

            if (redemption.isNewParticipant) {
                // leave the conversation
                await removeConversationParticipant({
                    conversationId: redemption.conversationId,
                    participantId: 'me',
                });
            }

            // navigate to the newly duplicated conversation
            const conversationId = duplicatedConversationIds[0];
            navigate(`/conversation/${conversationId}`, { replace: true });
        } finally {
            setSubmitted(false);
        }
    }, [redeemShare, conversationShare, navigate, workbenchService, removeConversationParticipant, setSubmitted]);

    React.useEffect(() => {
        if (conversationShare && conversationShare.isRedeemable && conversationShare.metadata['openMessageAction']) {
            setMessageId(conversationShare.metadata['openMessageAction']);
            handleClickJoin();
        }
    }, [conversationShare, handleClickJoin, setMessageId]);

    const handleDismiss = React.useCallback(() => {
        navigate(`/`);
    }, [navigate]);

    const renderAppView = React.useCallback(
        (options: {
            dialogTitle?: string;
            dialogContent?: JSX.Element;
            dialogActions?: JSX.Element;
            dismissLabel?: string;
        }) => {
            const { dialogTitle, dialogContent, dialogActions, dismissLabel } = options;
            return (
                <AppView title={title}>
                    <Dialog open={true}>
                        <DialogSurface>
                            <DialogBody>
                                {dialogTitle && <DialogTitle>{dialogTitle}</DialogTitle>}
                                {dialogContent && <DialogContent>{dialogContent}</DialogContent>}
                                <DialogActions>
                                    <DialogTrigger>
                                        <Button onClick={handleDismiss}>{dismissLabel ?? 'Cancel'}</Button>
                                    </DialogTrigger>
                                    {dialogActions}
                                </DialogActions>
                            </DialogBody>
                        </DialogSurface>
                    </Dialog>
                </AppView>
            );
        },
        [handleDismiss],
    );

    const renderTrigger = React.useCallback(
        (options: {
            label: string;
            appearance?: 'secondary' | 'primary' | 'outline' | 'subtle' | 'transparent';
            onClick: () => void;
        }) => {
            return (
                <DialogTrigger>
                    <Button
                        style={{ width: 'max-content' }}
                        appearance={options?.appearance ?? 'primary'}
                        onClick={options.onClick}
                        disabled={submitted}
                    >
                        {options.label}
                    </Button>
                </DialogTrigger>
            );
        },
        [submitted],
    );

    if (conversationIsLoading) {
        return renderAppView({
            dialogContent: <Loading />,
        });
    }

    // Handle error states - either an explicit error or a missing conversation share after loading.
    if (conversationShareError || !conversationShare) {
        return renderAppView({
            dialogTitle: 'Share does not exist or has been deleted',
        });
    }

    // Determine the share type and render the appropriate view.
    const shareType = conversationUtility.getShareType(conversationShare);
    const { conversationTitle, createdByUser } = conversationShare;

    // Many of the share types have common content, so we'll define them here.
    const shareDetails = (
        <ul>
            <li>
                Conversation title: <strong>{conversationTitle}</strong>
            </li>
            <li>
                Shared by: <strong>{createdByUser.name}</strong>
            </li>
        </ul>
    );
    const inviteTitle = 'A conversation has been shared with you';
    const inviteContent = (
        <>
            You have been <em>{shareType.toLowerCase()}</em> a conversation:
            {shareDetails}
        </>
    );
    const copyNote = 'You may create a copy of the conversation to make changes without affecting the original.';

    switch (shareType) {
        // Handle the case where the share is no longer redeemable.
        case ConversationShareType.NotRedeemable:
            return renderAppView({
                dialogTitle: 'Share is no longer redeemable',
                dialogContent: (
                    <p>
                        The share has already been redeemed or has expired.
                        {shareDetails}
                        If you believe this is an error, please contact the person who shared the conversation with you.
                    </p>
                ),
            });

        // Handle the case where the user has been invited to participate in the conversation.
        case ConversationShareType.InvitedToParticipate:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <p>
                            {inviteContent}
                            By joining, you will be able to view and participate in the conversation.
                        </p>
                        <p>{copyNote}</p>
                    </>
                ),
                dialogActions: (
                    <>
                        {renderTrigger({
                            label: 'Create copy',
                            onClick: handleClickDuplicate,
                            appearance: 'secondary',
                        })}
                        {renderTrigger({
                            label: 'Join',
                            onClick: handleClickJoin,
                        })}
                    </>
                ),
            });

        // Handle the case where the user has been invited to observe the conversation.
        case ConversationShareType.InvitedToObserve:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <p>
                            {inviteContent}
                            By observing, you will be able to view the conversation without participating.
                        </p>
                        <p>{copyNote}</p>
                    </>
                ),
                dialogActions: (
                    <>
                        {renderTrigger({
                            label: 'Create copy',
                            onClick: handleClickDuplicate,
                            appearance: 'secondary',
                        })}
                        {renderTrigger({
                            label: 'Observe',
                            onClick: handleClickJoin,
                        })}
                    </>
                ),
            });

        // Handle the case where the user has been invited to duplicate the conversation.
        case ConversationShareType.InvitedToDuplicate:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <p>
                        {inviteContent}
                        {copyNote}
                    </p>
                ),
                dialogActions: renderTrigger({
                    label: 'Create copy',
                    onClick: handleClickDuplicate,
                }),
            });
    }
};
