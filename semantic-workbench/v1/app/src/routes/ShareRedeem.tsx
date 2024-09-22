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

    if (!conversationShareId) {
        throw new Error('Conversation Share ID is required');
    }

    const siteUtility = useSiteUtility();
    const { data: conversationShare, error: conversationShareError } = useGetShareQuery(conversationShareId);

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

    const handleCancel = React.useCallback(() => {
        navigate(`/`);
    }, [navigate]);

    if (conversationShareError) {
        return (
            <AppView title={title}>
                <Dialog open={true}>
                    <DialogSurface>
                        <DialogBody>
                            <DialogTitle>Share does not exist or has been deleted</DialogTitle>
                            <DialogContent></DialogContent>
                            <DialogActions>
                                <DialogTrigger>
                                    <Button onClick={handleCancel}>Home</Button>
                                </DialogTrigger>
                            </DialogActions>
                        </DialogBody>
                    </DialogSurface>
                </Dialog>
            </AppView>
        );
    }

    if (!conversationShare) {
        return (
            <AppView title={title}>
                <Dialog open={true}>
                    <DialogSurface>
                        <DialogBody>
                            <DialogTitle>Loading...</DialogTitle>
                            <DialogContent></DialogContent>
                        </DialogBody>
                    </DialogSurface>
                </Dialog>
            </AppView>
        );
    }

    const isRedeemable = conversationShare.isRedeemable;
    const showJoinAction = conversationShare.metadata['showJoinAction'] !== false;
    const showDuplicateAction = conversationShare.metadata['showDuplicateAction'] !== false;

    return (
        <AppView title={title}>
            <Dialog open={true}>
                <DialogSurface>
                    <DialogBody>
                        <DialogTitle>A conversation has been shared with you</DialogTitle>
                        <DialogContent>
                            {isRedeemable && (
                                <>
                                    {showJoinAction && (
                                        <p>
                                            You have been invited to{' '}
                                            <em>
                                                {conversationShare?.conversationPermission === 'read'
                                                    ? 'observe'
                                                    : 'join'}
                                            </em>{' '}
                                            a conversation:
                                            <ul>
                                                <li>
                                                    Conversation title:{' '}
                                                    <strong>{conversationShare?.conversationTitle}</strong>
                                                </li>
                                                <li>
                                                    Shared by: <strong>{conversationShare?.createdByUser.name}</strong>
                                                </li>
                                            </ul>
                                            {conversationShare?.conversationPermission === 'read' ? (
                                                <>
                                                    By observing, you will be able to view the conversation but not
                                                    participate in it.
                                                </>
                                            ) : (
                                                <>
                                                    By joining, you will be able to view and participate in the
                                                    conversation.
                                                </>
                                            )}
                                        </p>
                                    )}
                                    {showDuplicateAction && (
                                        <>
                                            <p>
                                                You have been invited to <em>create a copy</em> of a conversation:
                                                <ul>
                                                    <li>
                                                        Conversation title:{' '}
                                                        <strong>{conversationShare?.conversationTitle}</strong>
                                                    </li>
                                                    <li>
                                                        Shared by:{' '}
                                                        <strong>{conversationShare?.createdByUser.name}</strong>
                                                    </li>
                                                </ul>
                                                By creating a copy, you will be able to make changes without affecting
                                                the original conversation.
                                            </p>
                                        </>
                                    )}
                                </>
                            )}
                        </DialogContent>
                        <DialogActions>
                            <DialogTrigger>
                                <Button onClick={handleCancel}>Cancel</Button>
                            </DialogTrigger>
                            {showJoinAction && (
                                <DialogTrigger>
                                    <Button appearance="primary" onClick={handleClickJoin} disabled={submitted}>
                                        {conversationShare?.conversationPermission === 'read' ? 'Observe' : 'Join'}
                                    </Button>
                                </DialogTrigger>
                            )}
                            {showDuplicateAction && (
                                <DialogTrigger>
                                    <Button appearance="primary" onClick={handleClickDuplicate} disabled={submitted}>
                                        Create
                                    </Button>
                                </DialogTrigger>
                            )}
                        </DialogActions>
                    </DialogBody>
                </DialogSurface>
            </Dialog>
        </AppView>
    );
};
