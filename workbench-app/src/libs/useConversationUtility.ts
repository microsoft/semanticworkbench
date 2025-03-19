import dayjs from 'dayjs';
import debug from 'debug';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Constants } from '../Constants';
import { Conversation } from '../models/Conversation';
import { ConversationShare } from '../models/ConversationShare';
import { useAppSelector } from '../redux/app/hooks';
import { useUpdateConversationMutation } from '../services/workbench';

const log = debug(Constants.debug.root).extend('useConversationUtility');

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
    const [isMessageVisible, setIsMessageVisible] = React.useState(false);
    const isMessageVisibleRef = React.useRef(null);
    const [updateConversation] = useUpdateConversationMutation();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const navigate = useNavigate();

    // region Navigation

    const navigateToConversation = React.useCallback(
        (conversationId?: string, hash?: string) => {
            let path = conversationId ? '/' + conversationId : '';
            if (hash) {
                path += `#${hash}`;
            }
            navigate(path);
        },
        [navigate],
    );

    // endregion

    // region Shares
    //
    // This region contains logic for handling conversation shares, including determining the share type
    // based on the conversation permission and metadata. It also contains logic for handling the combinations
    // of metadata, permissions, and share types in shared location for consistency across the app.
    //

    const getOwnerParticipant = React.useCallback((conversation: Conversation) => {
        const owner = conversation.participants.find((participant) => participant.id === conversation.ownerId);
        if (!owner) {
            throw new Error('Owner not found in conversation participants');
        }
        return owner;
    }, []);

    const wasSharedWithMe = React.useCallback(
        (conversation: Conversation): boolean => {
            return conversation.ownerId !== localUserId;
        },
        [localUserId],
    );

    const getShareTypeMetadata = React.useCallback(
        (
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
        },
        [],
    );

    const getShareType = React.useCallback(
        (
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
        },
        [],
    );

    const getShareLink = React.useCallback((share: ConversationShare): string => {
        return `${window.location.origin}/conversation-share/${encodeURIComponent(share.id)}/redeem`;
    }, []);
    // endregion

    // region App Metadata

    const setAppMetadata = React.useCallback(
        async (conversation: Conversation, appMetadata: Partial<ParticipantAppMetadata>) => {
            if (!localUserId) {
                log(
                    'Local user ID not set while setting conversation metadata for user, skipping',
                    `[Conversation ID: ${conversation.id}]`,
                    appMetadata,
                );
                return;
            }

            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            const userAppMetadata = participantAppMetadata[localUserId] ?? {};

            // Save the conversation
            await updateConversation({
                id: conversation.id,
                metadata: {
                    ...conversation.metadata,
                    participantAppMetadata: {
                        ...participantAppMetadata,
                        [localUserId]: { ...userAppMetadata, ...appMetadata },
                    },
                },
            });
        },
        [updateConversation, localUserId],
    );

    // endregion

    // region Unread

    React.useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setIsMessageVisible(entry.isIntersecting);
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
            if (!localUserId) {
                return;
            }
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[localUserId]?.lastReadTimestamp;
        },
        [localUserId],
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
            return dayjs(lastMessageTimestamp).isAfter(lastReadTimestamp);
        },
        [getLastReadTimestamp, getLastMessageTimestamp],
    );

    const isUnread = React.useCallback(
        (conversation: Conversation, messageTimestamp: string) => {
            const lastReadTimestamp = getLastReadTimestamp(conversation);
            if (!lastReadTimestamp) {
                return true;
            }
            return dayjs(messageTimestamp).isAfter(lastReadTimestamp);
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

    const markAllAsUnread = React.useCallback(
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
            if (Array.isArray(conversation)) {
                await Promise.all(conversation.map((c) => setAppMetadata(c, { lastReadTimestamp: messageTimestamp })));
                return;
            }
            await setAppMetadata(conversation, { lastReadTimestamp: messageTimestamp });
        },
        [setAppMetadata],
    );

    // Create a debounced version of setLastRead
    const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);
    const debouncedSetLastRead = React.useCallback(
        (conversation: Conversation | Conversation[], messageTimestamp: string) => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            timeoutRef.current = setTimeout(() => setLastRead(conversation, messageTimestamp), 300);
        },
        [setLastRead],
    );

    // endregion

    // region Pinning

    const isPinned = React.useCallback(
        (conversation: Conversation) => {
            if (!localUserId) return;
            const participantAppMetadata: Record<string, ParticipantAppMetadata> =
                conversation.metadata?.participantAppMetadata ?? {};
            return participantAppMetadata[localUserId]?.pinned;
        },
        [localUserId],
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
        getOwnerParticipant,
        wasSharedWithMe,
        getShareTypeMetadata,
        getShareType,
        getShareLink,
        isMessageVisibleRef,
        isMessageVisible,
        hasUnreadMessages,
        isUnread,
        markAllAsRead,
        markAllAsUnread,
        setLastRead,
        debouncedSetLastRead,
        isPinned,
        setPinned,
    };
};
