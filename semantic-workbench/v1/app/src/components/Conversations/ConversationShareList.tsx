// Copyright (c) Microsoft. All rights reserved.

import { Field } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useGetSharesQuery } from '../../services/workbench/share';
import { MyShares } from './MyShares';

interface ConversationShareListProps {
    conversation: Conversation;
}

export const ConversationShareList: React.FC<ConversationShareListProps> = (props) => {
    const { conversation } = props;
    const { data: conversationShares, error: conversationSharesError } = useGetSharesQuery({
        conversationId: conversation.id,
        includeUnredeemable: false,
    });

    if (!conversation) {
        throw new Error('Conversation is required');
    }

    if (conversationSharesError) {
        throw new Error(`Error loading conversation shares: ${JSON.stringify(conversationSharesError)}`);
    }

    return (
        <>
            <Field>
                <MyShares
                    conversation={conversation}
                    shares={conversationShares ?? []}
                    title={`Shares for "${conversation.title}"`}
                />
            </Field>
        </>
    );
};
