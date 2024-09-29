import { ConversationShare } from '../../models/ConversationShare';
import { ConversationShareRedemption } from '../../models/ConversationShareRedemption';
import { workbenchApi } from './workbench';

const shareApi = workbenchApi.injectEndpoints({
    endpoints: (builder) => ({
        createShare: builder.mutation<
            ConversationShare,
            Pick<ConversationShare, 'conversationId' | 'label' | 'conversationPermission' | 'metadata'>
        >({
            query: (body) => ({
                url: '/conversation-shares',
                method: 'POST',
                body: transformConversationShareForRequest(body),
            }),
            invalidatesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShare(response),
        }),
        getShares: builder.query<
            ConversationShare[],
            { conversationId: string | undefined; includeUnredeemable: boolean }
        >({
            query: ({ conversationId, includeUnredeemable }) =>
                `/conversation-shares?include_unredeemable=${includeUnredeemable}` +
                (conversationId ? `&conversation_id=${conversationId}` : ''),
            providesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShares(response),
        }),
        getShare: builder.query<ConversationShare, string>({
            query: (conversationShareId: string) => `/conversation-shares/${encodeURIComponent(conversationShareId)}`,
            providesTags: ['ConversationShare'],
            transformResponse: (response: any) => transformResponseToConversationShare(response),
        }),
        deleteShare: builder.mutation<void, string>({
            query: (conversationShareId: string) => ({
                url: `/conversation-shares/${conversationShareId}`,
                method: 'DELETE',
            }),
            invalidatesTags: ['ConversationShare'],
        }),
        redeemShare: builder.mutation<ConversationShareRedemption, string>({
            query: (conversationShareId: string) => ({
                url: `/conversation-shares/${conversationShareId}/redemptions`,
                method: 'POST',
            }),
            // redeeming a share can add a user to a conversation
            invalidatesTags: ['ConversationShare', 'Conversation'],
            transformResponse: (response: any) => transformResponseToConversationShareRedemption(response),
        }),
    }),
    overrideExisting: false,
});

export const {
    useGetSharesQuery,
    useGetShareQuery,
    useDeleteShareMutation,
    useRedeemShareMutation,
    useCreateShareMutation,
} = shareApi;

const transformConversationShareForRequest = (
    newShare: Pick<ConversationShare, 'conversationId' | 'label' | 'conversationPermission' | 'metadata'>,
): any => {
    return {
        conversation_id: newShare.conversationId,
        label: newShare.label,
        conversation_permission: newShare.conversationPermission,
        metadata: newShare.metadata,
    };
};

const transformResponseToConversationShares = (response: any): ConversationShare[] => {
    try {
        return response.conversation_shares.map(transformResponseToConversationShare);
    } catch (error) {
        throw new Error(`Failed to transform shares response: ${error}`);
    }
};

const transformResponseToConversationShare = (response: any): ConversationShare => {
    try {
        return {
            id: response.id,
            createdByUser: response.created_by_user,
            label: response.label,
            conversationId: response.conversation_id,
            conversationTitle: response.conversation_title,
            conversationPermission: response.conversation_permission,
            isRedeemable: response.is_redeemable,
            createdDateTime: response.created_datetime,
            metadata: response.metadata,
        };
    } catch (error) {
        throw new Error(`Failed to transform share response: ${error}`);
    }
};

const transformResponseToConversationShareRedemption = (response: any): ConversationShareRedemption => {
    try {
        return {
            id: response.id,
            conversationId: response.conversation_id,
            conversationShareId: response.conversation_share_id,
            redeemedByUser: response.redeemed_by_user,
            conversationPermission: response.conversation_permission,
            createdDateTime: response.created_datetime,
            isNewParticipant: response.new_participant,
        };
    } catch (error) {
        throw new Error(`Failed to transform share response: ${error}`);
    }
};
