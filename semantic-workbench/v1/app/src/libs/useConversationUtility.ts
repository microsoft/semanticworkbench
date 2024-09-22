import { ConversationShare } from '../models/ConversationShare';

// Share types to be used in the app.
export const enum ConversationShareType {
    NotRedeemable = 'Not redeemable',
    InvitedToParticipate = 'Invited to participate',
    InvitedToObserve = 'Invited to observe',
    InvitedToDuplicate = 'Invited to copy',
}

export const useConversationUtility = () => {
    // region Conversation Shares
    //
    // This region contains logic for handling conversation shares, including determining the share type
    // based on the conversation permission and metadata. It also contains logic for handling the combinations
    // of metadata, permissions, and share types in shared location for consistency across the app.
    //
    const getShareTypeMetadata = (
        shareType: ConversationShareType,
    ): {
        permission: 'read' | 'read_write';
        metadata: { showDuplicateAction?: boolean };
    } => {
        // Default to read_write for invited to participate, read for observe or duplicate.
        const permission = shareType === ConversationShareType.InvitedToParticipate ? 'read_write' : 'read';
        const showDuplicateAction = shareType === ConversationShareType.InvitedToDuplicate;
        return {
            permission,
            metadata: { showDuplicateAction },
        };
    };

    const getShareType = (conversationShare: ConversationShare) => {
        const { isRedeemable, conversationPermission, metadata } = conversationShare;

        if (!isRedeemable) {
            return ConversationShareType.NotRedeemable;
        }

        // If the showDuplicateAction metadata is set, use that to determine the share type.
        if (!metadata.showDuplicateAction) {
            // Otherwise, use the conversation permission to determine the share type.
            return conversationPermission !== 'read'
                ? ConversationShareType.InvitedToParticipate
                : ConversationShareType.InvitedToObserve;
        }

        return ConversationShareType.InvitedToDuplicate;
    };
    // endregion

    // add more conversation related utility functions here, separated by region if applicable

    return {
        getShareTypeMetadata,
        getShareType,
    };
};
