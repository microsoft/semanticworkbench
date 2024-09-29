// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useGetSharesQuery } from '../../services/workbench/share';
import { Loading } from '../App/Loading';
import { MyShares } from './MyShares';

interface ConversationShareListProps {
    conversation: Conversation;
}

export const ConversationShareList: React.FC<ConversationShareListProps> = (props) => {
    const { conversation } = props;
    const {
        data: conversationShares,
        error: conversationSharesError,
        isLoading: conversationSharesLoading,
    } = useGetSharesQuery({
        conversationId: conversation.id,
        includeUnredeemable: false,
    });

    if (!conversation) {
        throw new Error('Conversation is required');
    }

    if (conversationSharesError) {
        throw new Error(`Error loading conversation shares: ${JSON.stringify(conversationSharesError)}`);
    }

    if (conversationSharesLoading || !conversationShares) {
        return <Loading />;
    }

    return (
        <MyShares
            conversation={conversation}
            shares={conversationShares}
            title={`Shares for "${conversation.title}"`}
        />
    );
};
