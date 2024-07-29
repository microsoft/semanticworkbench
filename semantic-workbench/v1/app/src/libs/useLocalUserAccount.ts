// Copyright (c) Microsoft. All rights reserved.

import { useAccount } from '@azure/msal-react';

export const useLocalUserAccount = () => {
    const account = useAccount();

    const getUserId = () => {
        // AAD accountID is <objectId>.<tenantId>, while the participantId is <tenantId>.<objectId>
        const userId = (account?.homeAccountId || '').split('.').reverse().join('.');

        if (!userId) {
            throw new Error('User ID is not available.');
        }

        return userId;
    };

    return {
        getUserId,
    };
};
