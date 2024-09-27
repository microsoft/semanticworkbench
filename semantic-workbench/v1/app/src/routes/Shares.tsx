// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { MyShares } from '../components/Conversations/MyShares';
import { useSiteUtility } from '../libs/useSiteUtility';
import { useGetSharesQuery } from '../services/workbench/share';

export const Shares: React.FC = () => {
    const {
        data: conversationShares,
        error: conversationSharesError,
        isLoading: isLoadingConversationShares,
    } = useGetSharesQuery({
        conversationId: undefined,
        includeUnredeemable: false,
    });

    const siteUtility = useSiteUtility();
    siteUtility.setDocumentTitle('Shares');

    if (conversationSharesError) {
        throw new Error(`Error loading conversation shares: ${JSON.stringify(conversationSharesError)}`);
    }

    if (isLoadingConversationShares) {
        return (
            <AppView title="Shares">
                <Loading />
            </AppView>
        );
    }

    return (
        <AppView title="Shares">
            <MyShares hideInstruction={true} shares={conversationShares ?? []} />
        </AppView>
    );
};
