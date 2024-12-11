// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { DialogControl } from '../components/App/DialogControl';
import { Loading } from '../components/App/Loading';
import { ConversationShareType, useConversationUtility } from '../libs/useConversationUtility';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useWorkbenchService } from '../libs/useWorkbenchService';
import { Conversation } from '../models/Conversation';
import { useAppSelector } from '../redux/app/hooks';
import {
    useCreateConversationMessageMutation,
    useGetConversationsQuery,
    useRemoveConversationParticipantMutation,
} from '../services/workbench';
import { useGetShareQuery, useRedeemShareMutation } from '../services/workbench/share';

export const ShareRedeem: React.FC = () => {
    const { conversationShareId } = useParams();
    const navigate = useNavigate();
    const workbenchService = useWorkbenchService();
    const [redeemShare] = useRedeemShareMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [joinAttempted, setJoinAttempted] = React.useState(false);
    const conversationUtility = useConversationUtility();
    const localUserName = useAppSelector((state) => state.localUser.name);

    if (!conversationShareId) {
        throw new Error('Conversation Share ID is required');
    }

    const siteUtility = useSiteUtility();
    const {
        data: conversationShare,
        error: conversationShareError,
        isLoading: conversationShareIsLoading,
    } = useGetShareQuery(conversationShareId);
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsIsLoading,
    } = useGetConversationsQuery();
    const [existingDuplicateConversations, setExistingDuplicateConversations] = React.useState<Array<Conversation>>([]);

    const title = 'Open a shared conversation';
    siteUtility.setDocumentTitle(title);

    const handleClickJoin = React.useCallback(
        async (messageId?: string) => {
            if (!conversationShare) {
                return;
            }
            setSubmitted(true);
            try {
                await redeemShare(conversationShare.id);
                const hash = messageId ? `#${messageId}` : '';

                // send event to notify the conversation that the user has joined
                if (conversationShare.conversationPermission === 'read_write') {
                    await createConversationMessage({
                        conversationId: conversationShare.conversationId,
                        content: `${localUserName} joined the conversation`,
                        messageType: 'notice',
                    });
                }

                conversationUtility.navigateToConversation(conversationShare.conversationId, hash);
            } finally {
                setSubmitted(false);
            }
        },
        [conversationShare, redeemShare, conversationUtility, createConversationMessage, localUserName],
    );

    const handleClickDuplicate = React.useCallback(async () => {
        if (!conversationShare) {
            return;
        }
        setSubmitted(true);
        try {
            // join the conversation
            const redemption = await redeemShare(conversationShare.id).unwrap();

            // duplicate it
            const duplicatedConversationIds = await workbenchService.exportThenImportConversationAsync([
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
            conversationUtility.navigateToConversation(conversationId);
        } finally {
            setSubmitted(false);
        }
    }, [conversationShare, redeemShare, workbenchService, conversationUtility, removeConversationParticipant]);

    const handleDismiss = React.useCallback(() => {
        navigate(`/`);
    }, [navigate]);

    const readyToCheckForMessageLink = conversationShare && !joinAttempted && !conversationsIsLoading;

    React.useEffect(() => {
        if (!readyToCheckForMessageLink) {
            return;
        }

        const { linkToMessageId } = conversationUtility.getShareType(conversationShare);
        if (!linkToMessageId) {
            return;
        }

        setJoinAttempted(true);
        handleClickJoin(linkToMessageId);
    }, [conversationShare, conversationUtility, handleClickJoin, readyToCheckForMessageLink]);

    const renderAppView = React.useCallback(
        (options: {
            dialogTitle?: string;
            dialogContent?: React.ReactElement;
            dialogActions?: React.ReactElement[];
            dismissLabel?: string;
        }) => {
            const { dialogTitle, dialogContent, dialogActions, dismissLabel } = options;
            return (
                <AppView title={title}>
                    <DialogControl
                        open={true}
                        onOpenChange={handleDismiss}
                        title={dialogTitle}
                        content={dialogContent}
                        closeLabel={dismissLabel ?? 'Close'}
                        additionalActions={dialogActions}
                    />
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
                <DialogTrigger disableButtonEnhancement>
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

    React.useEffect(() => {
        if (!conversations || !conversationShare) {
            return;
        }
        const existingDuplicates = conversations.filter(
            (conversation) => conversation.importedFromConversationId === conversationShare.conversationId,
        );
        if (existingDuplicates.length > 0) {
            setExistingDuplicateConversations(existingDuplicates);
        }
    }, [conversations, conversationShare]);

    if (conversationShareIsLoading || conversationsIsLoading) {
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

    if (conversationsError || !conversations) {
        return renderAppView({
            dialogTitle: 'Error loading conversations',
        });
    }

    // Determine the share type and render the appropriate view.
    const { shareType, linkToMessageId } = conversationUtility.getShareType(conversationShare);
    const { conversationTitle, createdByUser } = conversationShare;

    if (shareType !== ConversationShareType.NotRedeemable && linkToMessageId) {
        return renderAppView({
            dialogContent: <Loading />,
        });
    }

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
    const copyNote = 'You may create a copy of the conversation to make changes without affecting the original.';
    const existingCopyNote = existingDuplicateConversations.length ? (
        <>
            You have copied this conversation before. Click on a link below to open an existing copy:
            <ul>
                {existingDuplicateConversations.map((conversation) => (
                    <li key={conversation.id}>
                        <a
                            href={`${window.location.origin}/${conversation.id}`}
                        >
                            {conversation.title}
                        </a>
                    </li>
                ))}
            </ul>
        </>
    ) : (
        <> </>
    );

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
                            You have been <em>invited to participate</em> in a conversation: By joining, you will be
                            able to view and participate in the conversation.
                            {shareDetails}
                        </p>
                        <p>{existingCopyNote}</p>
                        <p>{copyNote}</p>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                        appearance: 'secondary',
                    }),
                    renderTrigger({
                        label: 'Join',
                        onClick: handleClickJoin,
                    }),
                ],
            });

        // Handle the case where the user has been invited to observe the conversation.
        case ConversationShareType.InvitedToObserve:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <p>
                            You have been <em>invited to observe</em> a conversation: By observing, you will be able to
                            view the conversation without participating.
                            {shareDetails}
                        </p>
                        <p>{existingCopyNote}</p>
                        <p>{copyNote}</p>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                        appearance: 'secondary',
                    }),
                    renderTrigger({
                        label: 'Observe',
                        onClick: handleClickJoin,
                    }),
                ],
            });

        // Handle the case where the user has been invited to duplicate the conversation.
        case ConversationShareType.InvitedToDuplicate:
            return renderAppView({
                dialogTitle: inviteTitle,
                dialogContent: (
                    <>
                        <p>
                            You have been <em>invited to copy</em> a conversation:
                            {shareDetails}
                        </p>
                        <p>{existingCopyNote}</p>
                        <p>{copyNote}</p>
                    </>
                ),
                dialogActions: [
                    renderTrigger({
                        label: 'Create copy',
                        onClick: handleClickDuplicate,
                    }),
                ],
            });
    }
};
