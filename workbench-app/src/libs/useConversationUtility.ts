import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Constants } from '../Constants';
import { Conversation } from '../models/Conversation';
import { ConversationShare } from '../models/ConversationShare';
import { useUpdateConversationMutation } from '../services/workbench';
import { useLocalUserAccount } from './useLocalUserAccount';
import { Utility } from './Utility';

// Share types to be used in the app.
export const enum ConversationShareType {
    NotRedeemable = 'Not redeemable',
    InvitedToParticipate = 'Invited to participate',
    InvitedToObserve = 'Invited to observe',
    InvitedToDuplicate = 'Invited to copy',
}

interface ParticipantAppMetadata {
    lastReadTimestamp?: string;
    pinned?: boolean;
}

export const useConversationUtility = () => {
    const [isMessageVisible, setIsVisible] = React.useState(false);
    const isMessageVisibleRef = React.useRef(null);
    const [updateConversation] = useUpdateConversationMutation();
    const { getUserId } = useLocalUserAccount();
    const userId = getUserId();
    const navigate = useNavigate();

    // region Navigation

    const navigateToConversation = (conversationId?: string) => {
        navigate([Constants.app.conversationRedirectPath, conversationId].join('/'));
    };

    // endregion

    // region Shares
    //
    // This region contains logic for handling conversation shares, including determining the share type
    // based on the conversation permission and metadata. It also contains logic for handling the combinations
    // of metadata, permissions, and share types in shared location for consistency across the app.
    //
    const getShareTypeMetadata = (
        shareType: ConversationShareType,
        linkToMessageId?: string,
    ): {
        permission: 'read' | 'read_write';
        metadata: { showDuplicateAction?: boolean; linkToMessageId?: string };
    } => {
        // Default to read_write for invited to participate, read for observe or duplicate.
        const permission = shareType === ConversationShareType.InvitedToParticipate ? 'read_write' : 'read';
        const showDuplicateAction = shareType === ConversationShareType.InvitedToDuplicate;
        return {
            permission,
            metadata: { showDuplicateAction, linkToMessageId },
        };
    };

    const getShareType = (
        conversationShare: ConversationShare,
    ): {
        shareType: ConversationShareType;
        linkToMessageId?: string;
    } => {
        const { isRedeemable, conversationPermission, metadata } = conversationShare;

        if (!isRedeemable) {
            return { shareType: ConversationShareType.NotRedeemable };
        }

        // If the showDuplicateAction metadata is set, use that to determine the share type.
        if (metadata.showDuplicateAction) {
            return { shareType: ConversationShareType.InvitedToDuplicate };
        }

        // Otherwise, use the conversation permission to determine the share type.
        const shareType =
            conversationPermission !== 'read'
                ? ConversationShareType.InvitedToParticipate
                : ConversationShareType.InvitedToObserve;
        return {
            shareType,
            linkToMessageId: metadata.linkToMessageId,
        };
    };

    const getShareLink = (share: ConversationShare): string => {
        return `${window.location.origin}/conversation-share/${encodeURIComponent(share.id)}/redeem`;
    };
    // endregion

    // region App Metadata

    const setAppMetadata = React.useCallback(
        async (conversation: Conversation, appMetadata: Partial<ParticipantAppMetadata>) => {
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            const userAppMetadata = participantAppMetadata[userId] ?? {};

            // Save the conversation
            await updateConversation({
                ...conversation,
                metadata: {
                    ...conversation.metadata,
                    participantAppMetadata: {
                        ...participantAppMetadata,
                        [userId]: { ...userAppMetadata, ...appMetadata },
                    },
                },
            });
        },
        [updateConversation, userId],
    );

    // endregion

    // region Unread

    React.useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsVisible(entry.isIntersecting);
            },
            { threshold: 0.1 },
        );

        const currentRef = isMessageVisibleRef.current;
        if (currentRef) {
            observer.observe(currentRef);
        }

        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
    }, []);

    const getLastReadTimestamp = React.useCallback(
        (conversation: Conversation) => {
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[userId]?.lastReadTimestamp;
        },
        [userId],
    );

    const getLastMessageTimestamp = React.useCallback((conversation: Conversation) => {
        return conversation.latest_message?.timestamp ?? conversation.created;
    }, []);

    const hasUnreadMessages = React.useCallback(
        (conversation: Conversation) => {
            const lastReadTimestamp = getLastReadTimestamp(conversation);
            if (!lastReadTimestamp) {
                return true;
            }
            const lastMessageTimestamp = getLastMessageTimestamp(conversation);
            return lastMessageTimestamp > lastReadTimestamp;
        },
        [getLastReadTimestamp, getLastMessageTimestamp],
    );

    const isUnread = React.useCallback(
        (conversation: Conversation, messageTimestamp: string) => {
            const lastReadTimestamp = getLastReadTimestamp(conversation);
            if (!lastReadTimestamp) {
                return true;
            }
            return messageTimestamp > lastReadTimestamp;
        },
        [getLastReadTimestamp],
    );

    const markAllAsRead = React.useCallback(
        async (conversation: Conversation | Conversation[]) => {
            const markSingleConversation = async (c: Conversation) => {
                if (!hasUnreadMessages(c)) {
                    return;
                }
                await setAppMetadata(c, { lastReadTimestamp: getLastMessageTimestamp(c) });
            };

            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map(markSingleConversation));
                return;
            }
            await markSingleConversation(conversation);
        },
        [hasUnreadMessages, setAppMetadata, getLastMessageTimestamp],
    );

    const markAsUnread = React.useCallback(
        async (conversation: Conversation | Conversation[]) => {
            const markSingleConversation = async (c: Conversation) => {
                if (hasUnreadMessages(c)) {
                    return;
                }
                await setAppMetadata(c, { lastReadTimestamp: undefined });
            };

            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map(markSingleConversation));
                return;
            }

            await markSingleConversation(conversation);
        },
        [hasUnreadMessages, setAppMetadata],
    );

    const setLastRead = React.useCallback(
        async (conversation: Conversation | Conversation[], messageTimestamp: string) => {
            const debouncedFunction = Utility.debounce(async () => {
                if (Array.isArray(conversation)) {
                    await Promise.all(
                        conversation.map((c) => setAppMetadata(c, { lastReadTimestamp: messageTimestamp })),
                    );
                    return;
                }
                await setAppMetadata(conversation, { lastReadTimestamp: messageTimestamp });
            }, 300);

            debouncedFunction();
        },
        [setAppMetadata],
    );

    // endregion

    // region Pinning

    const isPinned = React.useCallback(
        (conversation: Conversation) => {
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[userId]?.pinned;
        },
        [userId],
    );

    const setPinned = React.useCallback(
        async (conversation: Conversation | Conversation[], pinned: boolean) => {
            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map((c) => setAppMetadata(c, { pinned })));
                return;
            }
            await setAppMetadata(conversation, { pinned });
        },
        [setAppMetadata],
    );

    // endregion

    // add more conversation related utility functions here, separated by region if applicable

    return {
        navigateToConversation,
        getShareTypeMetadata,
        getShareType,
        getShareLink,
        isMessageVisibleRef,
        isMessageVisible,
        hasUnreadMessages,
        isUnread,
        markAllAsRead,
        markAsUnread,
        setLastRead,
        isPinned,
        setPinned,
    };
};
